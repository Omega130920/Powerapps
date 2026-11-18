import hashlib
import logging
import mimetypes
import os
import re
from email.message import EmailMessage as PyEmailMessage
from email.utils import format_datetime
from dateutil import parser

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from ..models import (
    EmailDelegation,
    DelegationNote,
    DelegationTransactionLog,
    OutlookInbox,
    UnityInternalEmailAttachment,
)
from .outlook_graph_service import OutlookGraphService

User = get_user_model()
logger = logging.getLogger(__name__)


def _safe_filename(name, default="attachment.bin"):
    if not name:
        return default
    cleaned = re.sub(r'[\\/*?:"<>|\r\n]+', '_', str(name)).strip()
    return cleaned[:180] or default


def _email_storage_dir(email_id, received_dt=None):
    dt = received_dt or timezone.now()
    email_hash = hashlib.sha1(str(email_id).encode('utf-8')).hexdigest()[:20]
    rel_dir = os.path.join('email_archive', dt.strftime('%Y'), dt.strftime('%m'), email_hash)
    abs_dir = os.path.join(settings.MEDIA_ROOT, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)
    return rel_dir, abs_dir


def download_and_link_attachments(target_email, email_id, body_html="", received_dt=None):
    """
    Fetches attachment metadata from Graph, streams each attachment to disk in 8 KB chunks,
    creates UnityInternalEmailAttachment rows, and rewrites inline cid: references in body_html
    to local protected Django URLs.
    """
    attachments_meta = OutlookGraphService.fetch_attachments(target_email, email_id)
    if not attachments_meta:
        return body_html or "", False

    rel_dir, abs_dir = _email_storage_dir(email_id, received_dt)
    updated_html = body_html or ""
    has_non_inline = False

    for att in attachments_meta:
        att_id = att.get('id')
        if not att_id:
            continue

        raw_name = _safe_filename(att.get('name'), default=f"{att_id[:12]}.bin")
        content_type = att.get('contentType') or 'application/octet-stream'
        size = int(att.get('size') or 0)
        content_id = (att.get('contentId') or '').strip('<> ').strip() or None
        raw_is_inline = bool(att.get('isInline', False))
        # Only hide from attachment gallery if it's genuinely an inline CID image embedded in the HTML body
        is_inline = bool(raw_is_inline and content_id and (content_id.lower() in (body_html or '').lower()))

        existing_att = UnityInternalEmailAttachment.objects.filter(
            email_id=email_id,
            attachment_id=att_id
        ).first()

        if not existing_att:
            att_hash = hashlib.md5(att_id.encode('utf-8')).hexdigest()[:8]
            disk_name = f"{att_hash}_{raw_name}"
            rel_file_path = os.path.join(rel_dir, disk_name).replace('\\', '/')
            abs_file_path = os.path.join(abs_dir, disk_name)

            file_stream = OutlookGraphService.stream_attachment_mime(target_email, email_id, att_id)
            if file_stream:
                try:
                    with open(abs_file_path, 'wb') as f:
                        for chunk in file_stream:
                            if chunk:
                                f.write(chunk)

                    existing_att = UnityInternalEmailAttachment.objects.create(
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
                    logger.error(f"Failed writing attachment {raw_name} for {email_id}: {e}")

        if existing_att:
            if not existing_att.is_inline:
                has_non_inline = True

            if existing_att.content_id and updated_html:
                local_url = reverse('serve_local_attachment', kwargs={'att_pk': existing_att.id})
                cid_clean = re.escape(existing_att.content_id)
                updated_html = re.sub(
                    rf'cid:{cid_clean}',
                    local_url,
                    updated_html,
                    flags=re.IGNORECASE
                )

    return updated_html, has_non_inline


def download_raw_eml_to_disk(target_email, email_id, received_dt=None):
    """
    Streams the raw .eml RFC822 message from Graph in 8 KB chunks to disk
    and returns the relative media path.
    """
    rel_dir, abs_dir = _email_storage_dir(email_id, received_dt)
    rel_eml_path = os.path.join(rel_dir, 'message.eml').replace('\\', '/')
    abs_eml_path = os.path.join(abs_dir, 'message.eml')

    if os.path.exists(abs_eml_path) and os.path.getsize(abs_eml_path) > 0:
        return rel_eml_path

    eml_stream = OutlookGraphService.stream_raw_eml(target_email, email_id)
    if not eml_stream:
        return None

    try:
        with open(abs_eml_path, 'wb') as f:
            for chunk in eml_stream:
                if chunk:
                    f.write(chunk)
        return rel_eml_path
    except Exception as e:
        logger.error(f"Failed saving raw .eml for {email_id}: {e}")
        return None


def ingest_single_email_from_graph(target_email, email_id, msg_payload=None):
    """
    Ingests a single email into OutlookInbox, EmailDelegation, and UnityInternalEmailAttachment.
    Once is_fully_synced=True, Unity Internal never needs to call Graph for this email again.
    """
    existing_inbox = OutlookInbox.objects.filter(email_id=email_id).first()
    if existing_inbox and existing_inbox.is_fully_synced:
        get_or_create_delegation_status(email_id, received_dt=existing_inbox.received_at)
        return existing_inbox

    msg = msg_payload
    if not msg or 'body' not in msg:
        msg = OutlookGraphService.fetch_message_details(target_email, email_id)
        if not isinstance(msg, dict) or 'error' in msg:
            logger.warning(f"Could not fetch full details from Graph for {email_id}: {msg}")
            return existing_inbox

    subject = msg.get('subject') or '(No Subject)'
    sender_info = msg.get('from', {}).get('emailAddress', {})
    sender_name = sender_info.get('name') or ''
    sender_addr = sender_info.get('address') or ''
    snippet = (msg.get('bodyPreview') or '')[:500]
    body_html = msg.get('body', {}).get('content') or ''
    has_attachments_flag = bool(msg.get('hasAttachments', False))

    received_str = msg.get('receivedDateTime')
    received_dt = None
    if received_str:
        try:
            received_dt = parser.isoparse(received_str)
        except Exception:
            received_dt = parse_datetime(received_str)
    if not received_dt:
        received_dt = timezone.now()

    to_list = [
        r.get('emailAddress', {}).get('address', '')
        for r in msg.get('toRecipients', [])
        if r.get('emailAddress', {}).get('address')
    ]
    cc_list = [
        r.get('emailAddress', {}).get('address', '')
        for r in msg.get('ccRecipients', [])
        if r.get('emailAddress', {}).get('address')
    ]
    bcc_list = [
        r.get('emailAddress', {}).get('address', '')
        for r in msg.get('bccRecipients', [])
        if r.get('emailAddress', {}).get('address')
    ]

    # Download attachments or inline CID images if present
    has_non_inline = False
    if has_attachments_flag or ('cid:' in body_html.lower()):
        body_html, has_non_inline = download_and_link_attachments(
            target_email,
            email_id,
            body_html=body_html,
            received_dt=received_dt
        )

    eml_rel_path = download_raw_eml_to_disk(target_email, email_id, received_dt=received_dt)

    inbox_obj, _ = OutlookInbox.objects.update_or_create(
        email_id=email_id,
        defaults={
            'subject': subject,
            'sender_name': sender_name,
            'sender_address': sender_addr,
            'snippet': snippet,
            'to_addresses': ", ".join(to_list),
            'cc_addresses': ", ".join(cc_list),
            'bcc_addresses': ", ".join(bcc_list),
            'body_content': body_html,
            'has_attachments': has_attachments_flag or has_non_inline,
            'received_at': received_dt,
            'eml_file_path': eml_rel_path,
            'is_fully_synced': True,
        }
    )

    get_or_create_delegation_status(email_id, received_dt=received_dt)
    return inbox_obj


def sync_new_inbox_emails(target_email=None, top_count=50):
    """
    Fast inbox sync: makes ONE lightweight call to Microsoft Graph for the latest messages,
    skips any email_id already in OutlookInbox/EmailDelegation, and saves new arrivals
    immediately so /outlook/ loads in under 1 second.
    Heavy attachments and .eml files are downloaded on-demand when an email is opened/delegated.
    """
    mailbox = target_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', '')
    inbox_data = OutlookGraphService.fetch_inbox_messages(mailbox, top_count=top_count)

    if not isinstance(inbox_data, dict) or 'error' in inbox_data:
        return inbox_data

    all_messages = inbox_data.get('value', [])
    if not all_messages:
        return {'synced': 0}

    incoming_ids = [m.get('id') for m in all_messages if m.get('id')]

    existing_inbox_ids = set(
        OutlookInbox.objects.filter(email_id__in=incoming_ids).values_list('email_id', flat=True)
    )
    existing_delegation_ids = set(
        EmailDelegation.objects.filter(email_id__in=incoming_ids).values_list('email_id', flat=True)
    )

    new_inbox_rows = []
    new_delegation_rows = []
    synced_count = 0

    for msg in all_messages:
        e_id = msg.get('id')
        if not e_id:
            continue

        received_str = msg.get('receivedDateTime')
        received_dt = None
        if received_str:
            try:
                received_dt = parser.isoparse(received_str)
            except Exception:
                received_dt = parse_datetime(received_str)
        if not received_dt:
            received_dt = timezone.now()

        if e_id not in existing_inbox_ids:
            subject = msg.get('subject') or '(No Subject)'
            sender_info = msg.get('from', {}).get('emailAddress', {})
            sender_name = sender_info.get('name') or ''
            sender_addr = sender_info.get('address') or ''
            snippet = (msg.get('bodyPreview') or '')[:500]
            body_html = msg.get('body', {}).get('content') or ''
            has_atts = bool(msg.get('hasAttachments', False))

            to_list = [
                r.get('emailAddress', {}).get('address', '')
                for r in msg.get('toRecipients', [])
                if r.get('emailAddress', {}).get('address')
            ]
            cc_list = [
                r.get('emailAddress', {}).get('address', '')
                for r in msg.get('ccRecipients', [])
                if r.get('emailAddress', {}).get('address')
            ]
            bcc_list = [
                r.get('emailAddress', {}).get('address', '')
                for r in msg.get('bccRecipients', [])
                if r.get('emailAddress', {}).get('address')
            ]

            # Only mark is_fully_synced=True right away if there are no attachments or inline cid: images to fetch
            needs_attachment_download = has_atts or ('cid:' in body_html.lower())

            new_inbox_rows.append(
                OutlookInbox(
                    email_id=e_id,
                    subject=subject[:512],
                    sender_name=sender_name[:255],
                    sender_address=sender_addr[:255],
                    snippet=snippet,
                    to_addresses=", ".join(to_list),
                    cc_addresses=", ".join(cc_list),
                    bcc_addresses=", ".join(bcc_list),
                    body_content=body_html,
                    has_attachments=has_atts,
                    received_at=received_dt,
                    eml_file_path=None,
                    is_fully_synced=not needs_attachment_download,
                )
            )
            existing_inbox_ids.add(e_id)
            synced_count += 1

        if e_id not in existing_delegation_ids:
            new_delegation_rows.append(
                EmailDelegation(
                    email_id=e_id,
                    status='NEW',
                    work_related=True,
                    received_at=received_dt,
                )
            )
            existing_delegation_ids.add(e_id)

    if new_inbox_rows:
        OutlookInbox.objects.bulk_create(new_inbox_rows, ignore_conflicts=True)
    if new_delegation_rows:
        EmailDelegation.objects.bulk_create(new_delegation_rows, ignore_conflicts=True)

    return {'synced': synced_count}


def _build_outlook_eml_bytes(subject, sender_email, recipient_email, cc_email, bcc_email, sent_dt, html_body, attachment_tuples=None):
    """
    Builds an Outlook-compatible RFC822 .eml byte stream using Compat32(max_line_length=None)
    so long MIME types (like .xlsx / .docx) are never corrupted with =?utf-8?q?...?= encoding,
    and uses a single clean text/html body part (no ugly text/plain fallback).
    attachment_tuples: list of (filename, content_type, file_bytes)
    """
    from email.message import EmailMessage as PyEmailMessage
    from email import policy as email_policy
    from email.utils import format_datetime, make_msgid

    clean_mime_policy = email_policy.Compat32(max_line_length=None, linesep='\r\n')
    msg = PyEmailMessage()
    msg['Subject'] = (subject or '(No Subject)').replace('\r', ' ').replace('\n', ' ').strip()
    msg['From'] = sender_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'unityeb@futurasa.co.za')
    msg['To'] = recipient_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'unityeb@futurasa.co.za')
    if cc_email and str(cc_email).strip() not in ('', '-', 'None'):
        msg['Cc'] = str(cc_email).strip()
    if bcc_email and str(bcc_email).strip() not in ('', '-', 'None'):
        msg['Bcc'] = str(bcc_email).strip()

    dt = sent_dt or timezone.now()
    msg['Date'] = format_datetime(timezone.localtime(dt) if timezone.is_aware(dt) else dt)
    msg['Message-ID'] = make_msgid(domain='futurasa.co.za')

    # Strip any nested <!DOCTYPE>, <html>, <head>, or <body> tags from quoted history so Outlook renders one clean document
    cleaned_inner = html_body or ''
    cleaned_inner = re.sub(r'<!DOCTYPE[^>]*>', '', cleaned_inner, flags=re.IGNORECASE)
    cleaned_inner = re.sub(r'</?(html|head|body)[^>]*>', '', cleaned_inner, flags=re.IGNORECASE)
    cleaned_inner = re.sub(r'<meta[^>]*>', '', cleaned_inner, flags=re.IGNORECASE)

    wrapped_html = (
        '<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head>'
        f'<body style="font-family: Calibri, Arial, sans-serif; font-size: 11pt; color: #000000;">{cleaned_inner}</body></html>'
    )
    msg.set_content(wrapped_html, subtype='html', charset='utf-8')

    if attachment_tuples:
        for fname, c_type, f_bytes in attachment_tuples:
            safe_ctype = (c_type or '').strip().lower()
            if not safe_ctype or '/' not in safe_ctype:
                guessed, _ = mimetypes.guess_type(fname or '')
                safe_ctype = guessed or 'application/octet-stream'
            maintype, subtype = safe_ctype.split('/', 1)
            msg.add_attachment(f_bytes, maintype=maintype, subtype=subtype, filename=fname)

    return msg.as_bytes(policy=clean_mime_policy)


def save_outgoing_email_locally(
    owner_key,
    sender_email,
    recipient_email,
    cc_email,
    bcc_email,
    subject,
    html_body,
    uploaded_files=None,
    sent_dt=None
):
    """
    Saves outgoing Reply (REPLY_<tx_id>) or Direct (DIRECT_<note_id>) attachments to disk
    in 8 KB chunks, registers them in UnityInternalEmailAttachment, and builds a clean
    Outlook-compatible RFC822 .eml file on disk.
    """
    sent_dt = sent_dt or timezone.now()
    rel_dir, abs_dir = _email_storage_dir(owner_key, sent_dt)
    attachment_tuples = []

    if uploaded_files:
        for idx, up_file in enumerate(uploaded_files):
            try:
                safe_name = _safe_filename(up_file.name, default=f"file_{idx}.bin")
                disk_name = f"out_{idx}_{safe_name}"
                rel_file_path = os.path.join(rel_dir, disk_name).replace('\\', '/')
                abs_file_path = os.path.join(abs_dir, disk_name)

                up_file.seek(0)
                file_size = 0
                with open(abs_file_path, 'wb') as f:
                    for chunk in up_file.chunks(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            file_size += len(chunk)

                c_type = getattr(up_file, 'content_type', None) or mimetypes.guess_type(safe_name)[0] or 'application/octet-stream'

                UnityInternalEmailAttachment.objects.create(
                    email_id=owner_key,
                    attachment_id=f"local_{idx}",
                    name=safe_name,
                    content_type=c_type,
                    size=file_size,
                    is_inline=False,
                    content_id=None,
                    file_path=rel_file_path
                )

                with open(abs_file_path, 'rb') as rf:
                    attachment_tuples.append((safe_name, c_type, rf.read()))

                up_file.seek(0)
            except Exception as e:
                logger.error(f"Failed saving outgoing attachment for {owner_key}: {e}")

    rel_eml_path = os.path.join(rel_dir, f"{owner_key}.eml").replace('\\', '/')
    abs_eml_path = os.path.join(abs_dir, f"{owner_key}.eml")
    try:
        eml_bytes = _build_outlook_eml_bytes(
            subject=subject,
            sender_email=sender_email,
            recipient_email=recipient_email,
            cc_email=cc_email,
            bcc_email=bcc_email,
            sent_dt=sent_dt,
            html_body=html_body,
            attachment_tuples=attachment_tuples,
        )
        with open(abs_eml_path, 'wb') as ef:
            ef.write(eml_bytes)
    except Exception as e:
        logger.error(f"Failed generating outgoing .eml for {owner_key}: {e}")
        rel_eml_path = None

    return rel_eml_path


def get_or_create_delegation_status(email_id, received_date_str=None, received_dt=None):
    """
    Retrieves the existing EmailDelegation record or creates a new one with status 'NEW'.
    Prevents duplicate rows if multiple records exist for the same email_id.
    """
    existing = EmailDelegation.objects.filter(email_id=email_id).order_by('id').first()
    if existing:
        return existing

    defaults = {'status': 'NEW'}
    if received_dt:
        defaults['received_at'] = received_dt
    elif received_date_str:
        try:
            defaults['received_at'] = parser.isoparse(received_date_str)
        except Exception as e:
            logger.warning(f"Error parsing date {received_date_str} for {email_id}: {e}")

    return EmailDelegation.objects.create(email_id=email_id, **defaults)


@transaction.atomic
def delegate_email_task(email_id, assigned_user_pk, delegator_user, classification_data):
    """
    Assigns an email task to a user, classifies it using the provided data,
    and locks the status to 'DEL' across any duplicate rows for that email_id.
    """
    try:
        delegation = get_or_create_delegation_status(email_id)
        assigned_user = User.objects.get(pk=assigned_user_pk)
        now_ts = timezone.now()

        work_rel = classification_data.get('work_related')
        if isinstance(work_rel, str):
            work_rel = (work_rel == 'Yes')
        else:
            work_rel = bool(work_rel)

        delegation.assigned_user = assigned_user
        delegation.status = 'DEL'
        delegation.delegated_at = now_ts
        delegation.work_related = work_rel
        delegation.email_category = classification_data.get('email_category')
        delegation.communication_type = classification_data.get('comm_type') or 'Email'
        delegation.company_code = classification_data.get('company_code')
        delegation.save()

        # Ensure no stray duplicate 'NEW' rows remain for the same email_id
        EmailDelegation.objects.filter(email_id=email_id).exclude(pk=delegation.pk).update(
            assigned_user=assigned_user,
            status='DEL',
            delegated_at=now_ts,
            work_related=work_rel,
            email_category=delegation.email_category,
            communication_type=delegation.communication_type,
            company_code=delegation.company_code,
        )

        DelegationNote.objects.create(
            delegation=delegation,
            user=delegator_user,
            content=(
                f"Delegated to {assigned_user.username}. "
                f"Category: {delegation.email_category}, "
                f"Company Code: {delegation.company_code or 'None'}"
            )
        )

        return True, f"Task successfully delegated to {assigned_user.username}."

    except User.DoesNotExist:
        return False, "Assigned user not found."
    except Exception as e:
        logger.exception(f"ERROR during delegation of {email_id}")
        return False, f"An unexpected error occurred during delegation: {e}"


def add_delegation_note(delegation_id, user, content):
    """Adds a note against a delegated email task."""
    if not content:
        return False, "Note content cannot be empty."

    try:
        delegation = EmailDelegation.objects.get(pk=delegation_id)
        DelegationNote.objects.create(
            delegation=delegation,
            user=user,
            content=content
        )
        return True, "Note added successfully."
    except EmailDelegation.DoesNotExist:
        return False, "Delegation record not found."


def get_delegated_emails_for_user(user):
    """Retrieves all active email tasks delegated to the current user."""
    return EmailDelegation.objects.filter(
        assigned_user=user,
        status__in=['DEL', 'PEN']
    ).order_by('-delegated_at')


def log_delegation_transaction(
    delegation_id,
    user,
    subject,
    recipient_email,
    action_type='EMAIL_REPLY',
    body=None,
    cc_recipients=None,
    bcc_recipients=None,
    attached_file=None,
    eml_file_path=None
):
    """Creates a record in the DelegationTransactionLog and returns (True, message, tx_obj)."""
    try:
        delegation = EmailDelegation.objects.get(pk=delegation_id)
        safe_subject = subject if subject else (delegation.email_category or f"Task {delegation.id} Action")
        safe_recipient = recipient_email if recipient_email else "Internal/System"

        tx_obj = DelegationTransactionLog.objects.create(
            delegation=delegation,
            user=user,
            subject=safe_subject[:255],
            recipient_email=safe_recipient,
            cc_recipients=cc_recipients,
            bcc_recipients=bcc_recipients,
            action_type=action_type,
            body=body,
            attached_file=attached_file,
            eml_file_path=eml_file_path,
        )
        return True, "Transaction logged successfully.", tx_obj
    except EmailDelegation.DoesNotExist:
        return False, "Delegation record not found for logging.", None
    except Exception as e:
        logger.exception("Error logging delegation transaction")
        return False, f"Error logging transaction: {e}", None