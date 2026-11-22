import hashlib
import logging
import mimetypes
import os
import re
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.policy import Compat32
from email.utils import format_datetime, make_msgid

from dateutil import parser
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.text import get_valid_filename

from acvv.models import (
    AcvvEmailAttachment,
    DelegationNote,
    DelegationTransactionLog,
    EmailDelegation,
)
from acvv.services.outlook_graph_service import OutlookGraphService

logger = logging.getLogger(__name__)


# ==============================================================================
# LOCAL STORAGE & HELPER UTILITIES
# ==============================================================================

def _get_email_storage_dir(email_id):
    """
    Returns (relative_dir, absolute_dir) inside MEDIA_ROOT/email_archive/acvv/
    using a SHA-256 hash so long/special Microsoft Graph IDs never break file paths.
    """
    digest = hashlib.sha256(str(email_id).encode('utf-8')).hexdigest()
    rel_dir = os.path.join('email_archive', 'acvv', digest[:2], digest).replace('\\', '/')
    abs_dir = os.path.join(settings.MEDIA_ROOT, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)
    return rel_dir, abs_dir


def _format_graph_recipients(recip_list):
    """Extracts comma-separated email addresses from a Graph recipients list."""
    if not isinstance(recip_list, list):
        return ""
    addresses = []
    for r in recip_list:
        if isinstance(r, dict):
            addr = (r.get('emailAddress') or {}).get('address', '').strip()
            if addr:
                addresses.append(addr)
    return ", ".join(addresses)


def _safe_parse_dt(dt_val):
    """Safely parses an ISO datetime string or returns an existing datetime."""
    if not dt_val:
        return None
    if hasattr(dt_val, 'strftime'):
        return dt_val
    try:
        parsed = parser.isoparse(str(dt_val))
        if timezone.is_naive(parsed):
            parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed
    except Exception:
        return None


def _get_local_attachment_url(att_pk):
    """Builds the protected local attachment URL safely."""
    try:
        return reverse('serve_local_attachment', args=[att_pk])
    except Exception:
        return f"/attachments/local/{att_pk}/"


# ==============================================================================
# SYNC-ONCE LOCAL INGESTION ENGINE (8 KB STREAMING)
# ==============================================================================

def download_raw_eml_to_disk(email_id, target_email=None):
    """
    Streams the raw RFC822 .eml file from Microsoft Graph in 8 KB chunks directly
    to MEDIA_ROOT/email_archive/acvv/ so server RAM stays flat.
    Returns the relative path inside MEDIA_ROOT, or None on failure.
    """
    if not email_id or str(email_id).startswith(('SENT-', 'REPLY-', 'LOCAL-', 'CLAIM-', 'DIRECT_')):
        return None

    rel_dir, abs_dir = _get_email_storage_dir(email_id)
    rel_path = f"{rel_dir}/original.eml"
    abs_path = os.path.join(abs_dir, "original.eml")

    # Reuse if already downloaded and non-empty
    if os.path.exists(abs_path) and os.path.getsize(abs_path) > 0:
        return rel_path

    eml_stream = OutlookGraphService.stream_raw_eml(target_email, email_id, chunk_size=8192)
    if not eml_stream:
        return None

    try:
        written = 0
        with open(abs_path, 'wb') as f:
            for chunk in eml_stream:
                if chunk:
                    f.write(chunk)
                    written += len(chunk)
        if written > 0:
            return rel_path
        if os.path.exists(abs_path):
            os.remove(abs_path)
    except Exception as e:
        logger.error(f"Failed streaming raw .eml for {email_id}: {e}")
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
            except Exception:
                pass
    return None


def download_and_link_attachments(email_id, body_html, target_email=None, has_attachments=False):
    """
    Fetches attachment metadata from Graph (only if has_attachments is True OR 'cid:'
    appears in the HTML body), streams each file to disk in 8 KB chunks, saves records
    in AcvvEmailAttachment, and rewrites inline cid: references to protected local URLs.
    Returns (rewritten_body_html, has_non_inline_attachments).
    """
    body_html = body_html or ""
    has_cid_refs = 'cid:' in body_html.lower()

    if not has_attachments and not has_cid_refs:
        return body_html, False

    att_list = OutlookGraphService.fetch_attachments(target_email, email_id)
    if not att_list:
        return body_html, False

    rel_dir, abs_dir = _get_email_storage_dir(email_id)
    has_non_inline = False

    for idx, att in enumerate(att_list):
        att_id = att.get('id')
        if not att_id:
            continue

        raw_name = att.get('name') or f"attachment_{idx + 1}"
        content_type = att.get('contentType') or mimetypes.guess_type(raw_name)[0] or 'application/octet-stream'
        size = int(att.get('size') or 0)
        content_id = (att.get('contentId') or '').strip('<> ').strip() or None
        raw_is_inline = bool(att.get('isInline', False))

        # Safeguard: only hide from the attachment gallery if it is genuinely embedded via cid: in body_html
        is_inline = bool(raw_is_inline and content_id and (content_id.lower() in body_html.lower()))

        existing_att = AcvvEmailAttachment.objects.filter(
            email_id=email_id,
            attachment_id=att_id
        ).first()

        if existing_att:
            abs_existing = os.path.join(settings.MEDIA_ROOT, existing_att.file_path)
            if not os.path.exists(abs_existing):
                existing_att.delete()
                existing_att = None

        if not existing_att:
            safe_name = get_valid_filename(raw_name) or f"attachment_{idx + 1}"
            file_name = f"{idx + 1}_{safe_name}"
            rel_file_path = f"{rel_dir}/{file_name}"
            abs_file_path = os.path.join(abs_dir, file_name)

            file_stream = OutlookGraphService.stream_attachment_mime(target_email, email_id, att_id, chunk_size=8192)
            if not file_stream:
                continue

            try:
                written = 0
                with open(abs_file_path, 'wb') as f:
                    for chunk in file_stream:
                        if chunk:
                            f.write(chunk)
                            written += len(chunk)

                if written == 0 and size > 0:
                    if os.path.exists(abs_file_path):
                        os.remove(abs_file_path)
                    continue

                existing_att = AcvvEmailAttachment.objects.create(
                    email_id=email_id,
                    attachment_id=att_id,
                    name=raw_name[:255],
                    content_type=content_type[:150],
                    size=written or size,
                    is_inline=is_inline,
                    content_id=content_id[:255] if content_id else None,
                    file_path=rel_file_path,
                )
            except Exception as e:
                logger.error(f"Failed downloading attachment {raw_name} for {email_id}: {e}")
                continue
        else:
            # Keep inline flag accurate on existing records
            if existing_att.is_inline != is_inline:
                existing_att.is_inline = is_inline
                existing_att.save(update_fields=['is_inline'])

        if not existing_att.is_inline:
            has_non_inline = True

        # Rewrite cid:<content_id> references inside body_html to protected local URL
        if content_id and existing_att:
            local_url = _get_local_attachment_url(existing_att.id)
            pattern = re.compile(r'cid:' + re.escape(content_id), re.IGNORECASE)
            body_html = pattern.sub(local_url, body_html)

    return body_html, has_non_inline

def _normalize_dt_utc(dt_val):
    """Converts a datetime to timezone-aware UTC for reliable comparison."""
    if not dt_val:
        return None
    if timezone.is_naive(dt_val):
        return timezone.make_aware(dt_val, timezone.utc)
    return dt_val.astimezone(timezone.utc)


def _is_duplicate_worked_email(subject, sender_addr, received_dt, worked_index):
    """
    Returns True if (subject, sender_address) already exists in worked_index
    with a received_at matching within ±5s OR shifted by exactly 2 hours (±5s for SAST/UTC).
    """
    key = ((subject or '').strip().lower(), (sender_addr or '').strip().lower())
    worked_dates = worked_index.get(key)
    if not worked_dates:
        return False

    target_dt = _normalize_dt_utc(received_dt)
    if not target_dt:
        return True

    for w_dt in worked_dates:
        w_utc = _normalize_dt_utc(w_dt)
        if not w_utc:
            continue
        diff = abs((target_dt - w_utc).total_seconds())
        if diff <= 5 or abs(diff - 7200) <= 5:
            return True
    return False


def ingest_single_email_from_graph(email_id, target_email=None, msg_header=None, force_refresh=False):
    """
    Downloads a single incoming email from Microsoft Graph once:
    - Metadata (Subject, From Name/Address, To, CC, BCC, Received Date, Snippet)
    - Full HTML body with inline cid: images rewritten to local URLs
    - All attachments streamed to disk in 8 KB chunks
    - Raw .eml archive streamed to disk in 8 KB chunks
    Never resets or overwrites an existing worked status (DEL, COM, CLO, DLT, SENT).
    Returns the EmailDelegation instance or None if unavailable.
    """
    target_email = target_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'lorraine@futurasa.co.za')

    existing = EmailDelegation.objects.filter(email_id=email_id).first()
    if existing and existing.is_fully_synced and not force_refresh:
        # Backfill missing .eml on disk if needed
        if not existing.eml_file_path or not os.path.exists(os.path.join(settings.MEDIA_ROOT, existing.eml_file_path)):
            eml_rel = download_raw_eml_to_disk(email_id, target_email=target_email)
            if eml_rel:
                existing.eml_file_path = eml_rel
                existing.save(update_fields=['eml_file_path'])
        return existing

    # Fetch full message details from Graph
    msg_data = OutlookGraphService.fetch_message_details(target_email, email_id)
    if not isinstance(msg_data, dict) or 'error' in msg_data:
        if existing:
            return existing
        return None

    subject = (msg_data.get('subject') or (msg_header.get('subject') if msg_header else '') or '(No Subject)')[:255]
    from_info = (msg_data.get('from') or {}).get('emailAddress') or {}
    sender_address = (from_info.get('address') or '')[:255]
    sender_name = (from_info.get('name') or sender_address)[:255]
    snippet = (msg_data.get('bodyPreview') or '')[:512]
    to_recipients = _format_graph_recipients(msg_data.get('toRecipients', []))
    cc_recipients = _format_graph_recipients(msg_data.get('ccRecipients', []))
    bcc_recipients = _format_graph_recipients(msg_data.get('bccRecipients', []))
    received_at = _safe_parse_dt(msg_data.get('receivedDateTime'))
    raw_has_att = bool(msg_data.get('hasAttachments', False))

    body_obj = msg_data.get('body') or {}
    raw_body = body_obj.get('content') or ''
    if (body_obj.get('contentType') or '').lower() != 'html' and raw_body:
        raw_body = f"<pre style='white-space: pre-wrap; font-family: sans-serif;'>{raw_body}</pre>"

    # Duplicate/re-sync prevention: if this exact email already exists as a worked task under a different ID, skip creating a NEW duplicate
    if not existing and subject and sender_address and received_at:
        worked_dup = EmailDelegation.objects.filter(
            subject=subject,
            sender_address=sender_address,
            received_at=received_at
        ).exclude(status='NEW').first()
        if worked_dup:
            return worked_dup

    # Download attachments & rewrite inline cid: URLs
    rewritten_body, has_non_inline = download_and_link_attachments(
        email_id=email_id,
        body_html=raw_body,
        target_email=target_email,
        has_attachments=raw_has_att,
    )

    # Stream raw .eml backup to disk
    eml_rel_path = download_raw_eml_to_disk(email_id, target_email=target_email)

    if existing:
        existing.subject = existing.subject or subject
        existing.sender_address = existing.sender_address or sender_address
        existing.sender_name = sender_name or existing.sender_name
        existing.snippet = snippet or existing.snippet
        existing.to_recipients = to_recipients or existing.to_recipients
        existing.cc_recipients = cc_recipients or existing.cc_recipients
        existing.bcc_recipients = bcc_recipients or existing.bcc_recipients
        existing.received_at = existing.received_at or received_at
        existing.body = rewritten_body or existing.body
        existing.has_attachments = bool(has_non_inline or raw_has_att)
        if eml_rel_path:
            existing.eml_file_path = eml_rel_path
        existing.is_fully_synced = True
        existing.save()
        return existing

    return EmailDelegation.objects.create(
        email_id=email_id,
        subject=subject,
        sender_address=sender_address,
        sender_name=sender_name,
        snippet=snippet,
        to_recipients=to_recipients,
        cc_recipients=cc_recipients,
        bcc_recipients=bcc_recipients,
        received_at=received_at,
        body=rewritten_body,
        has_attachments=bool(has_non_inline or raw_has_att),
        eml_file_path=eml_rel_path,
        is_fully_synced=True,
        status='NEW',
        work_related=True,
    )


def sync_new_inbox_emails(target_email=None, top_count=200):
    """
    Polls Microsoft Graph for recent inbox message headers and fully ingests ONLY
    brand-new (or not-yet-synced) emails into local MySQL + disk storage.
    Never overwrites delegated, completed, or recycled items and blocks old-ID vs.
    ImmutableId duplicates (including 2-hour SAST/UTC offsets).
    Returns (synced_count, error_message_or_None).
    """
    target_email = target_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'lorraine@futurasa.co.za')
    inbox_data = OutlookGraphService.fetch_inbox_messages(target_email=target_email, top_count=top_count)

    if not isinstance(inbox_data, dict) or 'error' in inbox_data:
        err = inbox_data.get('error', 'Unknown Graph API error') if isinstance(inbox_data, dict) else 'Unknown Graph API error'
        return 0, err

    messages_list = inbox_data.get('value', [])
    if not messages_list:
        return 0, None

    incoming_ids = [m['id'] for m in messages_list if m.get('id')]

    # 1. Bulk lookup existing records by email_id
    existing_map = {
        row.email_id: row
        for row in EmailDelegation.objects.filter(email_id__in=incoming_ids)
    }

    # 2. Build normalized index of all worked (non-NEW) emails: {(subj, sender): [received_at, ...]}
    worked_index = {}
    for subj, sender, recv in EmailDelegation.objects.exclude(status='NEW').values_list('subject', 'sender_address', 'received_at'):
        key = ((subj or '').strip().lower(), (sender or '').strip().lower())
        worked_index.setdefault(key, []).append(recv)

    synced_count = 0
    for msg in messages_list:
        msg_id = msg.get('id')
        if not msg_id:
            continue

        existing = existing_map.get(msg_id)
        if existing and (existing.status != 'NEW' or existing.is_fully_synced):
            continue

        subj = (msg.get('subject') or '(No Subject)')[:255]
        sender_addr = ((msg.get('from') or {}).get('emailAddress') or {}).get('address', '')[:255]
        recv_dt = _safe_parse_dt(msg.get('receivedDateTime'))

        # Skip if this exact email already exists as a worked task under an older Graph ID
        if _is_duplicate_worked_email(subj, sender_addr, recv_dt, worked_index):
            if existing and existing.status == 'NEW':
                existing.delete()
            continue

        result = ingest_single_email_from_graph(
            email_id=msg_id,
            target_email=target_email,
            msg_header=msg,
        )
        if result:
            synced_count += 1

    return synced_count, None


# ==============================================================================
# LOCAL OUTGOING EMAIL & CLEAN RFC822 .EML ARCHIVER
# ==============================================================================

def build_clean_eml_bytes(subject, sender, recipient, html_body, cc=None, bcc=None, sent_dt=None, attachment_paths=None):
    """
    Builds a clean, Outlook-compatible RFC822 .eml file using Compat32(max_line_length=None)
    so HTML renders properly and long lines/headers never corrupt in Outlook.
    `attachment_paths` is an optional list of (display_name, abs_file_path, content_type) tuples.
    """
    msg = MIMEMultipart('mixed')
    msg['Subject'] = str(subject or '(No Subject)').replace('\r', ' ').replace('\n', ' ')
    msg['From'] = str(sender or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'acvv@futurasa.co.za'))
    msg['To'] = str(recipient or '')
    if cc:
        msg['Cc'] = str(cc)
    if bcc:
        msg['Bcc'] = str(bcc)

    dt_val = sent_dt or timezone.now()
    if timezone.is_naive(dt_val):
        dt_val = timezone.make_aware(dt_val, timezone.get_current_timezone())
    msg['Date'] = format_datetime(dt_val)
    msg['Message-ID'] = make_msgid(domain='futurasa.co.za')

    body_str = html_body or ""
    if '<html' not in body_str.lower():
        wrapped_html = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
            f"<body style=\"font-family: 'Segoe UI', Calibri, Arial, sans-serif; font-size: 14px;\">{body_str}</body></html>"
        )
    else:
        wrapped_html = body_str

    msg.attach(MIMEText(wrapped_html, 'html', 'utf-8'))

    if attachment_paths:
        for display_name, abs_path, ctype in attachment_paths:
            if not abs_path or not os.path.exists(abs_path):
                continue
            try:
                guessed_type = ctype or mimetypes.guess_type(display_name)[0] or 'application/octet-stream'
                if '/' in guessed_type:
                    maintype, subtype = guessed_type.split('/', 1)
                else:
                    maintype, subtype = 'application', 'octet-stream'

                with open(abs_path, 'rb') as f:
                    part = MIMEBase(maintype, subtype)
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=display_name)
                msg.attach(part)
            except Exception as e:
                logger.error(f"Failed attaching {display_name} to .eml: {e}")

    return msg.as_bytes(policy=Compat32(max_line_length=None))


def save_outgoing_email_locally(owner_key, subject, sender, recipient, html_body, cc=None, bcc=None, uploaded_files=None, sent_dt=None):
    """
    Saves all uploaded outgoing attachments to disk + AcvvEmailAttachment under `owner_key`
    and writes a complete RFC822 .eml archive to disk.
    Returns (eml_rel_path, saved_attachment_records).
    """
    rel_dir, abs_dir = _get_email_storage_dir(owner_key)
    saved_records = []
    att_tuples = []

    if uploaded_files:
        for idx, uf in enumerate(uploaded_files):
            if not uf:
                continue
            raw_name = getattr(uf, 'name', f'attachment_{idx + 1}')
            safe_name = get_valid_filename(raw_name) or f'attachment_{idx + 1}'
            file_name = f"out_{idx + 1}_{safe_name}"
            rel_file_path = f"{rel_dir}/{file_name}"
            abs_file_path = os.path.join(abs_dir, file_name)
            content_type = getattr(uf, 'content_type', None) or mimetypes.guess_type(raw_name)[0] or 'application/octet-stream'

            try:
                uf.seek(0)
                written = 0
                with open(abs_file_path, 'wb') as out_f:
                    for chunk in uf.chunks():
                        out_f.write(chunk)
                        written += len(chunk)
                uf.seek(0)

                att_rec = AcvvEmailAttachment.objects.create(
                    email_id=owner_key,
                    attachment_id=f"local_out_{idx + 1}_{int(timezone.now().timestamp())}",
                    name=raw_name[:255],
                    content_type=content_type[:150],
                    size=written,
                    is_inline=False,
                    content_id=None,
                    file_path=rel_file_path,
                )
                saved_records.append(att_rec)
                att_tuples.append((raw_name, abs_file_path, content_type))
            except Exception as e:
                logger.error(f"Failed saving outgoing attachment {raw_name} for {owner_key}: {e}")

    eml_bytes = build_clean_eml_bytes(
        subject=subject,
        sender=sender,
        recipient=recipient,
        html_body=html_body,
        cc=cc,
        bcc=bcc,
        sent_dt=sent_dt or timezone.now(),
        attachment_paths=att_tuples,
    )

    eml_rel_path = f"{rel_dir}/outgoing.eml"
    eml_abs_path = os.path.join(abs_dir, "outgoing.eml")
    try:
        with open(eml_abs_path, 'wb') as f:
            f.write(eml_bytes)
    except Exception as e:
        logger.error(f"Failed writing outgoing .eml for {owner_key}: {e}")
        eml_rel_path = None

    return eml_rel_path, saved_records


# ==============================================================================
# EXISTING DELEGATION & LOGGING FUNCTIONS (HARDENED)
# ==============================================================================

def get_or_create_delegation_status(email_id, received_date_str=None):
    """
    Retrieves the existing EmailDelegation record or creates a new one
    with status 'NEW' and saves the received date if provided.
    """
    try:
        delegation = EmailDelegation.objects.get(email_id=email_id)
    except EmailDelegation.DoesNotExist:
        defaults = {'status': 'NEW', 'work_related': True}
        if received_date_str:
            parsed = _safe_parse_dt(received_date_str)
            if parsed:
                defaults['received_at'] = parsed
        delegation = EmailDelegation.objects.create(email_id=email_id, **defaults)

    return delegation


@transaction.atomic
def delegate_email_task(email_id, assigned_user_pk, delegator_user, classification_data):
    """
    Assigns an email task to a user, classifies it using the provided data,
    and sets the status to 'Delegated' (silently — no auto-reply to client).
    """
    try:
        delegation = get_or_create_delegation_status(email_id)

        if delegation.status not in ('NEW', 'DEL'):
            return False, f"Task status is already {delegation.get_status_display()}."

        assigned_user = User.objects.get(pk=assigned_user_pk)

        delegation.assigned_user = assigned_user
        delegation.status = 'DEL'
        delegation.delegated_at = timezone.now()
        delegation.work_related = classification_data.get('work_related') == 'Yes'
        delegation.email_category = classification_data.get('email_category')
        delegation.communication_type = classification_data.get('comm_type')
        delegation.mip_names = classification_data.get('mip_names')
        delegation.save()

        DelegationNote.objects.create(
            delegation=delegation,
            user=delegator_user,
            content=(
                f"Delegated to {assigned_user.username}. "
                f"Category: {delegation.email_category}, "
                f"MIP: {delegation.mip_names or 'None'}"
            )
        )

        return True, f"Task successfully delegated to {assigned_user.username}."

    except User.DoesNotExist:
        return False, "Assigned user not found."
    except Exception as e:
        logger.error(f"ERROR during delegation of {email_id}: {e}")
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
        status__in=['DEL']
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
    eml_file_path=None,
):
    """Creates a record in the DelegationTransactionLog and returns (success, message_or_obj)."""
    try:
        delegation = EmailDelegation.objects.get(pk=delegation_id)
        safe_subject = (subject if subject else (delegation.email_category or f"Task {delegation.id} Action"))[:255]
        safe_recipient = (recipient_email if recipient_email else "Internal/System")[:255]

        tx = DelegationTransactionLog.objects.create(
            delegation=delegation,
            user=user,
            subject=safe_subject,
            recipient_email=safe_recipient,
            cc_recipients=cc_recipients or None,
            bcc_recipients=bcc_recipients or None,
            action_type=action_type,
            body=body,
            eml_file_path=eml_file_path,
        )
        return True, tx
    except EmailDelegation.DoesNotExist:
        return False, "Delegation record not found for logging."
    except Exception as e:
        logger.error(f"Error logging transaction for delegation {delegation_id}: {e}")
        return False, f"Error logging transaction: {e}"