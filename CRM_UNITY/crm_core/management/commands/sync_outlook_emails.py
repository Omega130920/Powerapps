import os
import re
import hashlib
import logging
from django.conf import settings
from django.utils.text import get_valid_filename
from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil import parser
from crm_core.models import CrmInbox, CrmDelegateTo, CrmEmailAttachment
from crm_core.services.outlook_graph_service import OutlookGraphService

logger = logging.getLogger(__name__)

def extract_addresses(recipient_list):
    """Safely extracts comma-separated email addresses from Microsoft Graph recipient array."""
    if not recipient_list or not isinstance(recipient_list, list):
        return ""
    addresses = [
        item.get('emailAddress', {}).get('address', '').strip()
        for item in recipient_list
        if isinstance(item, dict) and item.get('emailAddress', {}).get('address')
    ]
    return ", ".join(filter(None, addresses))


def _get_email_storage_dir(email_id, received_dt=None):
    """Creates and returns a safe relative and absolute directory path for storing an email's files."""
    dt = received_dt or timezone.now()
    email_hash = hashlib.sha256(email_id.encode('utf-8')).hexdigest()[:24]
    rel_dir = os.path.join('email_archive', dt.strftime('%Y'), dt.strftime('%m'), email_hash)
    abs_dir = os.path.join(settings.MEDIA_ROOT, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)
    return rel_dir, abs_dir


def download_and_link_attachments(email_id, body_html, received_dt=None, target_email=None):
    """
    Downloads all attachments (regular + inline CID images) to disk in 8KB chunks,
    saves CrmEmailAttachment rows, and rewrites cid: references in body_html to local URLs.
    """
    meta_endpoint = f"messages/{email_id}/attachments?$select=id,name,contentType,size,isInline,microsoft.graph.fileAttachment/contentId"
    meta_resp = OutlookGraphService._make_graph_request(meta_endpoint, target_email=target_email, method='GET')

    if not isinstance(meta_resp, dict) or 'error' in meta_resp:
        return body_html or "", False

    att_list = meta_resp.get('value', [])
    if not att_list:
        return body_html or "", False

    rel_dir, abs_dir = _get_email_storage_dir(email_id, received_dt)
    updated_html = body_html or ""
    has_non_inline = False

    for att in att_list:
        att_id = att.get('id')
        if not att_id:
            continue

        raw_name = att.get('name') or f"attachment_{att_id[:8]}"
        safe_name = get_valid_filename(raw_name) or f"attachment_{att_id[:8]}"
        content_id = (att.get('contentId') or '').strip('<>').strip()
        raw_is_inline = bool(att.get('isInline', False))
        # Only hide from attachment gallery if it's genuinely an inline CID image embedded in the HTML body
        is_inline = bool(raw_is_inline and content_id and (content_id.lower() in (body_html or '').lower()))
        content_id = (att.get('contentId') or '').strip('<>').strip()
        content_type = att.get('contentType') or 'application/octet-stream'
        size = int(att.get('size') or 0)

        # Check if already downloaded locally
        existing_att = CrmEmailAttachment.objects.filter(email_id=email_id, attachment_id=att_id).first()
        if not existing_att:
            rel_file_path = os.path.join(rel_dir, f"{att_id[:10]}_{safe_name}").replace('\\', '/')
            abs_file_path = os.path.join(settings.MEDIA_ROOT, rel_file_path)

            # Stream binary content via /$value in 8KB chunks using the generator from OutlookGraphService
            file_stream = OutlookGraphService.stream_attachment_mime(target_email, email_id, att_id)
            if file_stream:
                try:
                    with open(abs_file_path, 'wb') as f:
                        for chunk in file_stream:
                            if chunk:
                                f.write(chunk)

                    existing_att = CrmEmailAttachment.objects.create(
                        email_id=email_id,
                        attachment_id=att_id,
                        name=raw_name,
                        content_type=content_type,
                        size=size,
                        is_inline=is_inline,
                        content_id=content_id,
                        file_path=rel_file_path
                    )
                except Exception as e:
                    logger.error(f"Failed writing attachment {att_id} for email {email_id}: {e}")

        if existing_att:
            if not existing_att.is_inline:
                has_non_inline = True

            # Rewrite inline cid: image references in HTML to local protected endpoint
            local_url = f"/attachments/local/{existing_att.id}/"
            if content_id and updated_html:
                pattern = re.compile(r'cid:' + re.escape(content_id), re.IGNORECASE)
                updated_html = pattern.sub(local_url, updated_html)

    return updated_html, has_non_inline


def download_raw_eml_to_disk(email_id, received_dt=None, target_email=None):
    """Streams the raw MIME (.eml) file from Graph to local disk once during sync."""
    rel_dir, abs_dir = _get_email_storage_dir(email_id, received_dt)
    rel_eml_path = os.path.join(rel_dir, "original_message.eml").replace('\\', '/')
    abs_eml_path = os.path.join(settings.MEDIA_ROOT, rel_eml_path)

    if os.path.exists(abs_eml_path) and os.path.getsize(abs_eml_path) > 0:
        return rel_eml_path

    endpoint = f"messages/{email_id}/$value"
    resp = OutlookGraphService._make_graph_request(endpoint, target_email=target_email, method='GET', is_mime=True)
    if resp and hasattr(resp, 'status_code') and resp.status_code == 200:
        try:
            with open(abs_eml_path, 'wb') as f:
                if hasattr(resp, 'iter_content'):
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                else:
                    f.write(resp.content)
            return rel_eml_path
        except Exception as e:
            logger.warning(f"Failed to save local .eml for {email_id}: {e}")
        finally:
            if hasattr(resp, 'close'):
                resp.close()
    return None


def ingest_single_email_from_graph(msg_or_id, target_email=None):
    """
    Ingests or backfills a single email (either from a Graph message dict or by email_id string)
    into CrmInbox (and CrmDelegateTo if already delegated), downloading all attachments and .eml locally.
    Never resets an already-delegated or recycled email back to 'Pending'.
    """
    if isinstance(msg_or_id, str):
        email_id = msg_or_id
        endpoint = (
            f"messages/{email_id}?"
            f"$select=id,subject,from,toRecipients,ccRecipients,bccRecipients,receivedDateTime,bodyPreview,body,hasAttachments"
        )
        msg = OutlookGraphService._make_graph_request(endpoint, target_email=target_email, method='GET')
        if not isinstance(msg, dict) or 'error' in msg:
            return None
    else:
        msg = msg_or_id
        email_id = msg.get('id')
        if 'body' not in msg or 'ccRecipients' not in msg or 'toRecipients' not in msg:
            endpoint = (
                f"messages/{email_id}?"
                f"$select=id,subject,from,toRecipients,ccRecipients,bccRecipients,receivedDateTime,bodyPreview,body,hasAttachments"
            )
            full_msg = OutlookGraphService._make_graph_request(endpoint, target_email=target_email, method='GET')
            if isinstance(full_msg, dict) and 'error' not in full_msg:
                msg = full_msg

    if not email_id:
        return None

    raw_date = msg.get('receivedDateTime')
    local_date = timezone.localtime(parser.isoparse(raw_date)) if raw_date else timezone.now()

    from_obj = msg.get('from', {}).get('emailAddress', {}) if isinstance(msg.get('from'), dict) else {}
    sender_address = from_obj.get('address', 'Unknown')
    sender_name = from_obj.get('name', '') or sender_address

    body_data = msg.get('body', {}) if isinstance(msg.get('body'), dict) else {}
    body_content = body_data.get('content', '')
    if body_data.get('contentType', '').lower() == 'text' and body_content:
        body_content = f'<pre style="white-space: pre-wrap; font-family: sans-serif;">{body_content}</pre>'

    to_str = extract_addresses(msg.get('toRecipients', []))
    cc_str = extract_addresses(msg.get('ccRecipients', []))
    bcc_str = extract_addresses(msg.get('bccRecipients', []))
    has_att_flag = bool(msg.get('hasAttachments', False))

    # Download attachments or inline CID images if present
    if has_att_flag or ('cid:' in (body_content or '').lower()):
        body_content, has_non_inline = download_and_link_attachments(
            email_id, body_content, received_dt=local_date, target_email=target_email
        )
        has_att_flag = has_att_flag or has_non_inline

    # Download raw .eml backup to local disk
    eml_path = download_raw_eml_to_disk(email_id, received_dt=local_date, target_email=target_email)

    # Check if this email has already been delegated/recycled/completed so we NEVER reset its status to 'Pending'
    existing_delegation = CrmDelegateTo.objects.filter(email_id=email_id).first()
    existing_inbox = CrmInbox.objects.filter(email_id=email_id).first()

    inbox_defaults = {
        'subject': msg.get('subject') or 'No Subject',
        'sender': sender_address,
        'sender_name': sender_name,
        'snippet': (msg.get('bodyPreview') or '')[:500],
        'body_html': body_content,
        'has_attachments': has_att_flag,
        'to_recipients': to_str,
        'cc_recipients': cc_str,
        'bcc_recipients': bcc_str,
        'eml_file_path': eml_path,
        'is_fully_synced': True,
        'received_timestamp': local_date,
    }

    if existing_delegation:
        inbox_defaults['status'] = existing_delegation.status or 'Delegated'
        inbox_defaults['delegated_to'] = existing_delegation.delegated_to
        inbox_defaults['delegated_by'] = existing_delegation.delegated_by
        inbox_defaults['member_group_code'] = existing_delegation.member_group_code
    elif existing_inbox and existing_inbox.status and existing_inbox.status != 'Pending':
        inbox_defaults['status'] = existing_inbox.status

    inbox_entry, _ = CrmInbox.objects.update_or_create(
        email_id=email_id,
        defaults=inbox_defaults
    )

    # Also update CrmDelegateTo if this email was already delegated
    if existing_delegation:
        CrmDelegateTo.objects.filter(email_id=email_id).update(
            sender_name=sender_name,
            body_html=body_content,
            has_attachments=has_att_flag,
            to_recipients=to_str,
            cc_recipients=cc_str,
            bcc_recipients=bcc_str,
            eml_file_path=eml_path,
        )

    return inbox_entry


class Command(BaseCommand):
    help = 'Downloads new incoming emails, full HTML bodies, recipients, attachments, and .eml backups from Microsoft Graph to local storage'

    def handle(self, *args, **options):
        self.stdout.write("Starting Outlook email synchronization (Sync-Once, Render-Locally)...")

        inbox_data = OutlookGraphService.fetch_inbox_messages(top_count=100)

        if not isinstance(inbox_data, dict) or 'error' in inbox_data:
            err_msg = inbox_data.get('error', 'Unknown error') if isinstance(inbox_data, dict) else str(inbox_data)
            self.stderr.write(self.style.ERROR(f"Outlook Error: {err_msg}"))
            return

        emails = inbox_data.get('value', [])

        # Identify which emails are already fully synced OR already delegated/processed
        fully_synced_ids = set(
            CrmInbox.objects.filter(is_fully_synced=True).values_list('email_id', flat=True)
        )
        already_delegated_ids = set(
            CrmDelegateTo.objects.values_list('email_id', flat=True)
        )

        # Ensure any CrmInbox row that is already in CrmDelegateTo is not stuck on 'Pending'
        if already_delegated_ids:
            CrmInbox.objects.filter(email_id__in=already_delegated_ids, status='Pending').update(status='Delegated')

        new_count = 0
        for msg in emails:
            email_id = msg.get('id')
            if not email_id or email_id in fully_synced_ids or email_id in already_delegated_ids:
                continue

            entry = ingest_single_email_from_graph(msg)
            if entry:
                new_count += 1

        self.stdout.write(self.style.SUCCESS(f"Sync complete: {new_count} emails fully downloaded to local DB and disk."))