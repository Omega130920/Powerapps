import base64
import csv
import datetime
import json
import os
import mimetypes
import requests
import openpyxl
from base64 import urlsafe_b64decode, urlsafe_b64encode
from decimal import Decimal
from datetime import datetime, date, timezone as py_timezone
from dateutil import parser
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from django.template.loader import render_to_string
from django.http import StreamingHttpResponse, Http404, HttpResponse
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, Max
from django.http import FileResponse, Http404, HttpResponse, HttpRequest, JsonResponse
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.clickjacking import xframe_options_exempt
from django.core.paginator import Paginator
from django.db import connection, transaction
from django.forms.models import model_to_dict
from django.urls import reverse
import base64
import logging
logger = logging.getLogger(__name__)

# Model Imports
from .models import (
    ComplaintLog, CrmUnityOutlookToken, DirectEmail, DirectEmailLog, GlobalFundContact, Cbc, CbcAdminPerson, CbcConsultancyPerson,
    Cfa, CfaAdminPerson, Cfa2, Cfa3, CommunicationsPerson,
    HumanResources, Section13a, MedicalCorrespondence, ClientNotes,
    MemberDocument, CrmInbox, CrmEmailAttachment, CrmDelegateTo, CrmDelegateAction, DelegationReport
)
from .management.commands.sync_outlook_emails import ingest_single_email_from_graph

# Form Imports
from .forms import (
    DocumentUploadForm, ComplaintLogForm, GlobalFundContactForm, 
    CbcForm, CbcAdminPersonForm, CbcConsultancyPersonForm,
    CfaForm, CfaAdminPersonForm, Cfa2Form, Cfa3Form, 
    CommunicationsPersonForm, HumanResourcesForm, Section13aForm
)

from .models import MedicalCorrespondence 
from .forms import MedicalCorrespondenceForm
# Service Imports
from .services.outlook_graph_service import OutlookGraphService
from .services.delegation_service import delegate_email_task, add_action_note

User = get_user_model()
ZERO_DECIMAL = Decimal('0.00')


# --- GLOBAL MAPPINGS ---
CATEGORY_NAMES = {
    "1": "1. Reconciliation", "2": "2. Claims", "3": "3. Section 13A",
    "4": "4. New Business", "5": "5. Amendments", "6": "6. Section 28",
    "7": "7. Section 14", "8": "8. Section 27", "9": "9. Complaints",
    "10": "10. Two Pot", "11": "11. Report Back", "12": "12. Broker Investigations",
    "13": "13. General", "14": "14. Other"
}

ENQUIRY_GROUPING_MAP = {
    "1.1 Schedule Query": "Reconciliation (Queries, Sec 13A notices, Recon Queries)",
    "1.2 Member Data Query": "Reconciliation (Queries, Sec 13A notices, Recon Queries)",
    "1.3 Payment Query": "Reconciliation (Queries, Sec 13A notices, Recon Queries)",
    "1.4 Arrears Query": "Reconciliation (Queries, Sec 13A notices, Recon Queries)",
    "1.5 Online client RFW training Reconciliation": "RFW Training, SC Digital queries, New User Training",
    "1.6 Online Employer Amendment Data Query": "Reconciliation (Queries, Sec 13A notices, Recon Queries)",
    "1.7 Employer Data Referral for Overpayment": "Reconciliation (Queries, Sec 13A notices, Recon Queries)",
    "1.8 Employer Data Referral for Duplicate records and Merge queries": "Reconciliation (Queries, Sec 13A notices, Recon Queries)",
    "1.9 Member reinstatement": "Reconciliation (Queries, Sec 13A notices, Recon Queries)",
    "1.10 Member record Merge": "Reconciliation (Queries, Sec 13A notices, Recon Queries)",
    "2.1 Claim Form Query Active Withdrawal": "Claims (Two Pot included)",
    "2.2 Claim Form Receipt": "Claims (Two Pot included)",
    "2.3 Claim Form submission Active": "Claims (Two Pot included)",
    "2.4 Claim outstanding details": "Claims (Two Pot included)",
    "2.5 Claim Paid Confirmation": "Claims (Two Pot included)",
    "2.6 Forward Claim payment letter and tax documents": "Claims (Two Pot included)",
    "2.7 Claim Preservation Query": "Claims (Two Pot included)",
    "2.8 Claim ROT query": "Claims (Two Pot included)",
    "2.9 Claim Sec 14 query": "Claims (Two Pot included)",
    "2.10 Claim Paid Up Query": "Claims (Two Pot included)",
    "2.11  Emergency Two Pot Claim query": "Claims (Two Pot included)",
    "2.12 Retirement Claim query": "Claims (Two Pot included)",
    "2.13 Retirement Claim preservation Query": "Claims (Two Pot included)",
    "2.14 Retirement Claim Ill Health": "Claims (Two Pot included)",
    "2.15 Claim Paid Up Submission": "Claims (Two Pot included)",
    "2.16 Paid Up claim finalised (paid)": "Claims (Two Pot included)",
    "3.1  LPI  Section 13A Letter": "Reconciliation (Queries, Sec 13A notices, Recon Queries)",
    "3.2  Section 13A Client Query": "Reconciliation (Queries, Sec 13A notices, Recon Queries)",
    "3.3  Section 13A Termination": "Reconciliation (Queries, Sec 13A notices, Recon Queries)",
    "3.4 Section 13A Council Action": "Reconciliation (Queries, Sec 13A notices, Recon Queries)",
    "3.5 Section 13A Member Communication": "Reconciliation (Queries, Sec 13A notices, Recon Queries)",
    "3.6 Section 13A CBC Action": "Reconciliation (Queries, Sec 13A notices, Recon Queries)",
    "4.1 New Business Quote request": "New Business (Quotes, Installations and Queries)",
    "4.2 New Business COA and Accepted Quote submission": "New Business (Quotes, Installations and Queries)",
    "4.3 Welcome Email": "New Business (Quotes, Installations and Queries)",
    "4.4 Starter Pack Email": "New Business (Quotes, Installations and Queries)",
    "4.5 Starter Pack Meeting": "New Business (Quotes, Installations and Queries)",
    "4.6 Implementation confirmation": "New Business (Quotes, Installations and Queries)",
    "4.7 Employer Training": "RFW Training, SC Digital queries, New User Training",
    "5.1 Amendment Documentation": "Amendments",
    "5.2 Amendment to Acceptances": "Amendments",
    "5.3 Outstanding Amendment Documents": "Amendments",
    "5.4 Amendment Handover": "Amendments",
    "5.5 Amendment Rule to client broker": "Amendments",
    "5.6 Amendment COP to client broker": "Amendments",
    "5.7 Amendment RFW (Broker/Employer/3rd Party)": "Amendments",
    "6.1 Termination Query": "Terminations (Sec 14, 28 and 27)",
    "6.2 Termination Documentation Notice Letter": "Terminations (Sec 14, 28 and 27)",
    "6.3 Termination Banking Details for refund": "Terminations (Sec 14, 28 and 27)",
    "6.4 Termination Checklist": "Terminations (Sec 14, 28 and 27)",
    "6.5 Termination Withdrawal Forms": "Terminations (Sec 14, 28 and 27)",
    "6.6 Council confirmation of termination": "Terminations (Sec 14, 28 and 27)",
    "6.7 Member Termination Communication": "Terminations (Sec 14, 28 and 27)",
    "6.8 Section 14 Compulsory Form": "Terminations (Sec 14, 28 and 27)",
    "6.9 Section 14 Checklist": "Terminations (Sec 14, 28 and 27)",
    "6.10 Termination Fee Recovery": "Terminations (Sec 14, 28 and 27)",
    "7.1 Section 14 Query": "Terminations (Sec 14, 28 and 27)",
    "7.2 Section 14 Documentation": "Terminations (Sec 14, 28 and 27)",
    "7.3 Section 14 Outstanding requirements": "Terminations (Sec 14, 28 and 27)",
    "7.4 Section 14 Fund Query": "Terminations (Sec 14, 28 and 27)",
    "7.5 Section 14 Bank POP": "Terminations (Sec 14, 28 and 27)",
    "7.6 Section 14 Closure": "Terminations (Sec 14, 28 and 27)",
    "7.7 Section 14 Compulsory Form": "Terminations (Sec 14, 28 and 27)",
    "7.8 Section 14 Checklist": "Terminations (Sec 14, 28 and 27)",
    "7.9 Section 14 Member and Employer communication": "Terminations (Sec 14, 28 and 27)",
    "8.1 Termination Query": "Terminations (Sec 14, 28 and 27)",
    "8.2 Termination Documentation Notice Letter": "Terminations (Sec 14, 28 and 27)",
    "8.3 Termination Banking Details for refund": "Terminations (Sec 14, 28 and 27)",
    "8.4 Termination Checklist": "Terminations (Sec 14, 28 and 27)",
    "8.5 Termination Withdrawal Forms": "Terminations (Sec 14, 28 and 27)",
    "8.6 Council confirmation of termination": "Terminations (Sec 14, 28 and 27)",
    "8.7 Member Termination Communication (Retrenchment)": "Terminations (Sec 14, 28 and 27)",
    "8.8 Section 27 Compulsory Form": "Terminations (Sec 14, 28 and 27)",
    "8.9 Termination Member and Employer communication": "Terminations (Sec 14, 28 and 27)",
    "9.1 Complaint Detail Request": "Complaints (new 4)",
    "9.2 Complaint determination PFA": "Complaints (new 4)",
    "9.3 Member Complaint receipt and referral": "Complaints (new 4)",
    "9.4 Employer Complaint receipt and referral": "Complaints (new 4)",
    "9.5 Complaint Claim Payment": "Complaints (new 4)",
    "10.1 Employer Information Bulk Bank details": "Claims (Two Pot included)",
    "10.2 Employer Information Bulk Contact Details": "Claims (Two Pot included)",
    "10.3 Employer information Bulk Tax Detail changes": "Claims (Two Pot included)",
    "10.4 Training Employer Two Pot System changes": "RFW Training, SC Digital queries, New User Training",
    "10.5 Training Broker Two Pot Changes to Online": "RFW Training, SC Digital queries, New User Training",
    "10.6 Claim forms process query": "Claims (Two Pot included)",
    "10.7 Two Pot Process Claim Paid reports": "Claims (Two Pot included)",
    "10.8 Two Pot Member Claim Query": "Claims (Two Pot included)",
    "10.9  Two Pot Employer Query Reports for Qualifying Members": "Claims (Two Pot included)",
    "10.11 Two Pot Communication Employer Member Broker": "Claims (Two Pot included)",
    "11.1 Council Report Back": "Report Back (Broker and Employer Reports, Bulk Two Pot Communication)",
    "11.2 Broker Reports": "Report Back (Broker and Employer Reports, Bulk Two Pot Communication)",
    "11.3 Employer Reports": "Report Back (Broker and Employer Reports, Bulk Two Pot Communication)",
    "11.4 Sanlam Reports": "Report Back (Broker and Employer Reports, Bulk Two Pot Communication)",
    "11.5 Member Benefit Statement Monthly Reports": "General (Benefit statement CRM emails, New Claim forms generated etc, Commission Queries)",
    "11.6 Termination Report Back - Liquidations": "Report Back (Broker and Employer Reports, Bulk Two Pot Communication)",
    "11.7 Termination Report Back Clean Up Projects": "Report Back (Broker and Employer Reports, Bulk Two Pot Communication)",
    "11.8 Termination Report Back Dormant/Zero Members 2019 - 2024": "Report Back (Broker and Employer Reports, Bulk Two Pot Communication)",
    "12.1 Broker Investigation Letter": "Report Back (Broker and Employer Reports, Bulk Two Pot Communication)",
    "12.2 Broker Data and report Back Investigation Letter": "Report Back (Broker and Employer Reports, Bulk Two Pot Communication)",
    "12.3 Broker Client Reports for Claims Experience (Risk)": "Report Back (Broker and Employer Reports, Bulk Two Pot Communication)",
    "12.4 Broker Reports for Member Data, Underwriting and Claims Unresolved": "Report Back (Broker and Employer Reports, Bulk Two Pot Communication)",
    "13.1 Underwriting Queries": "Rate Revisions (CRM distribution of Rate letters, Queries)",
    "13.2 Death Claims Query": "Claims (Two Pot included)",
    "13.3 Funeral Claim Queries and notifications": "Claims (Two Pot included)",
    "13.4 Funeral Claim Outstanding Documents": "Claims (Two Pot included)",
    "13.5 Death Claim Outstanding Documents": "Claims (Two Pot included)",
    "13.6 Death Claim Beneficiary Fund Queries": "Claims (Two Pot included)",
    "13.7 Death Claim Distribution Approval to PE and Broker": "Claims (Two Pot included)",
    "13.8 AGRI Paid Up Funeral Claims": "Claims (Two Pot included)",
    "13.9 AGRI Paid Up Certificate Requests SGR": "Claims (Two Pot included)",
    "13.10 Repatriation Assistance to PE Family Broker": "Claims (Two Pot included)",
    "13.11 Funeral Claim Submission": "Claims (Two Pot included)",
    "13.12 Disability Query": "Claims (Two Pot included)",
    "13.13 Disability Application Submission": "Claims (Two Pot included)",
    "13.14 Disability Outstanding Reports": "Claims (Two Pot included)",
    "13.15 Disability Approval": "Claims (Two Pot included)",
    "13.16 Disability Declined": "Claims (Two Pot included)",
    "14.1 Bulk SMS to Members for documents, tax numbers": "General (Benefit statement CRM emails, New Claim forms generated etc, Commission Queries)",
    "14.2 Investment Reports for Brokers": "Report Back (Broker and Employer Reports, Bulk Two Pot Communication)",
    "14.3 Joint Forum Client Reports for PE and CBC": "Report Back (Broker and Employer Reports, Bulk Two Pot Communication)",
    "14.4 Divorce Orders - submission flagging": "General (Benefit statement CRM emails, New Claim forms generated etc, Commission Queries)",
    "14.5 Amendment to Member Guides - benefit changes": "General (Benefit statement CRM emails, New Claim forms generated etc, Commission Queries)",
    "14.7 Maintenance Orders - submission flagging": "General (Benefit statement CRM emails, New Claim forms generated etc, Commission Queries)",
    "14.8 Divorce order claim forms non member spouse": "General (Benefit statement CRM emails, New Claim forms generated etc, Commission Queries)",
    "14.9 Annual Rate Revision Data Preparation": "Rate Revisions (CRM distribution of Rate letters, Queries)",
    "14.10 Annual Rate Revision Amendments (AGR/Council etc)": "Rate Revisions (CRM distribution of Rate letters, Queries)",
    "14.11 Annual Rate Revision Distribution - PE Broker": "Rate Revisions (CRM distribution of Rate letters, Queries)",
    "14.12 Global List Monthly Checks and Amendments": "General (Benefit statement CRM emails, New Claim forms generated etc, Commission Queries)",
    "14.13 0101 Account Monthly Checks and Action": "General (Benefit statement CRM emails, New Claim forms generated etc, Commission Queries)",
    "14.14 Benefit Statement Query (member/employer)": "General (Benefit statement CRM emails, New Claim forms generated etc, Commission Queries)",
    "14.15 Bulk Benefit Statements (employer/member) ad-hoc": "General (Benefit statement CRM emails, New Claim forms generated etc, Commission Queries)",
}

# ==============================================================================
# AUTHENTICATION & DASHBOARD
# ==============================================================================

def _extract_attachments_from_local_eml(email_id, eml_rel_path, body_html, received_dt=None):
    """
    Self-healing fallback: parses the locally saved .eml file to extract any missing
    regular attachments (e.g. Screenshot.png) and inline CID images (e.g. image001.png),
    saving them to CrmEmailAttachment and rewriting cid: links in body_html.
    """
    import email
    from email import policy
    import re
    from django.utils.text import get_valid_filename
    from .management.commands.sync_outlook_emails import _get_email_storage_dir

    if not eml_rel_path:
        return body_html, False

    abs_eml_path = os.path.join(settings.MEDIA_ROOT, eml_rel_path)
    if not os.path.exists(abs_eml_path):
        return body_html, False

    try:
        with open(abs_eml_path, 'rb') as f:
            msg = email.message_from_binary_file(f, policy=policy.default)
    except Exception as e:
        logger.warning(f"Failed parsing local .eml for attachments ({email_id}): {e}")
        return body_html, False

    rel_dir, _ = _get_email_storage_dir(email_id, received_dt)
    updated_html = body_html or ""
    has_non_inline = False
    part_idx = 0

    for part in msg.walk():
        if part.is_multipart():
            continue

        content_disp = str(part.get("Content-Disposition", "") or "")
        content_id = str(part.get("Content-ID", "") or "").strip("<>").strip()
        filename = part.get_filename()

        is_inline = ("inline" in content_disp.lower()) or bool(content_id and not filename)
        if not filename and not content_id:
            continue

        if not filename and content_id:
            filename = content_id.split("@")[0] or f"inline_{part_idx}.png"

        part_idx += 1
        safe_name = get_valid_filename(filename) or f"att_{part_idx}"
        content_type = part.get_content_type() or "application/octet-stream"
        payload = part.get_payload(decode=True)
        if not payload:
            continue

        # Check if an attachment with this name/content_id already exists locally
        existing_att = CrmEmailAttachment.objects.filter(
            email_id=email_id,
            name=filename
        ).exclude(attachment_id__startswith='local_reply_').first()

        if not existing_att:
            rel_file_path = os.path.join(rel_dir, f"eml_{part_idx}_{safe_name}").replace('\\', '/')
            abs_file_path = os.path.join(settings.MEDIA_ROOT, rel_file_path)
            with open(abs_file_path, 'wb') as out_f:
                out_f.write(payload)

            existing_att = CrmEmailAttachment.objects.create(
                email_id=email_id,
                attachment_id=f"eml_att_{part_idx}_{safe_name}",
                name=filename,
                content_type=content_type,
                size=len(payload),
                is_inline=bool(is_inline and content_id and (f"cid:{content_id}".lower() in updated_html.lower())),
                content_id=content_id,
                file_path=rel_file_path
            )

        if existing_att:
            # If this CID is referenced inside the HTML body, rewrite cid: to local URL and mark inline
            if content_id and updated_html and (content_id.lower() in updated_html.lower()):
                local_url = f"/attachments/local/{existing_att.id}/"
                pattern = re.compile(r'cid:' + re.escape(content_id), re.IGNORECASE)
                updated_html = pattern.sub(local_url, updated_html)
                if not existing_att.is_inline:
                    existing_att.is_inline = True
                    existing_att.save(update_fields=['is_inline'])
            else:
                if existing_att.is_inline:
                    existing_att.is_inline = False
                    existing_att.save(update_fields=['is_inline'])
                has_non_inline = True

    return updated_html, has_non_inline

def get_crm_signature_details(user):
    """Returns the dynamic Name and Job Title based on the logged-in user."""
    username = user.username.lower() if user.username else ""
    first_name = user.first_name.lower() if user.first_name else ""
    
    # Default fallbacks
    agent_name = user.get_full_name() or user.username
    agent_title = "Administrator"
    
    # Match specific agents
    if 'gail' in username or 'gail' in first_name:
        agent_name = "Gail Le Roux"
        agent_title = "Client Relations Manager Sanlam Unity Umbrella Fund"
    elif 'merril' in username or 'merril' in first_name:
        agent_name = "Merril Fennessy"
        agent_title = "Client Relations Manager Sanlam Unity Umbrella Fund"
        
    return agent_name, agent_title


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})



def _ensure_local_email_data(email_id):
    """
    Returns (inbox_item, delegate_item, direct_item, body_html, attachments_list).
    Reads strictly from MySQL and local disk, and automatically backfills any missing
    attachments or unrewritten inline cid: images from Graph or the local .eml file.
    """
    import re
    inbox_item = CrmInbox.objects.filter(email_id=email_id).first()
    delegate_item = CrmDelegateTo.objects.filter(email_id=email_id).first()
    direct_item = DirectEmailLog.objects.filter(outlook_message_id=email_id).first() if not (inbox_item or delegate_item) else None

    body_html = (
        (delegate_item.body_html if delegate_item and delegate_item.body_html else None)
        or (inbox_item.body_html if inbox_item and inbox_item.body_html else None)
        or (direct_item.body_content if direct_item and direct_item.body_content else None)
    )

    existing_incoming_atts = (
        CrmEmailAttachment.objects
        .filter(email_id=email_id)
        .exclude(attachment_id__startswith='local_reply_')
    )
    has_unrewritten_cid = bool(body_html and ('cid:' in body_html.lower()))
    needs_att_sync = bool(
        ((inbox_item and inbox_item.has_attachments) or (delegate_item and delegate_item.has_attachments))
        and not existing_incoming_atts.filter(is_inline=False).exists()
    )

    # 1. If body is missing, or inline CID images weren't rewritten yet, or attachments weren't downloaded yet:
    if (not body_html or has_unrewritten_cid or needs_att_sync) and (inbox_item or delegate_item):
        try:
            synced_entry = ingest_single_email_from_graph(email_id)
            if synced_entry:
                inbox_item = synced_entry
                delegate_item = CrmDelegateTo.objects.filter(email_id=email_id).first()
                body_html = synced_entry.body_html or body_html
        except Exception as e:
            logger.warning(f"Graph backfill skipped for {email_id}: {e}")

    # 2. Self-healing from local .eml file if attachments or CID images are still missing
    eml_rel_path = getattr(inbox_item, 'eml_file_path', None) or getattr(delegate_item, 'eml_file_path', None)
    still_has_cid = bool(body_html and ('cid:' in body_html.lower()))
    still_missing_atts = not CrmEmailAttachment.objects.filter(email_id=email_id, is_inline=False).exclude(attachment_id__startswith='local_reply_').exists()

    if eml_rel_path and (still_has_cid or still_missing_atts):
        rec_dt = getattr(inbox_item, 'received_timestamp', None) or getattr(delegate_item, 'received_timestamp', None)
        new_html, found_non_inline = _extract_attachments_from_local_eml(email_id, eml_rel_path, body_html, received_dt=rec_dt)
        if new_html != body_html or found_non_inline:
            body_html = new_html
            if inbox_item:
                inbox_item.body_html = body_html
                if found_non_inline:
                    inbox_item.has_attachments = True
                inbox_item.save()
            if delegate_item:
                delegate_item.body_html = body_html
                if found_non_inline:
                    delegate_item.has_attachments = True
                delegate_item.save()

    # 3. Also rewrite any remaining cid: tags if matching CrmEmailAttachment rows already exist in DB
    if body_html and ('cid:' in body_html.lower()):
        for att_row in CrmEmailAttachment.objects.filter(email_id=email_id).exclude(content_id__isnull=True).exclude(content_id=''):
            local_url = f"/attachments/local/{att_row.id}/"
            pattern = re.compile(r'cid:' + re.escape(att_row.content_id), re.IGNORECASE)
            body_html = pattern.sub(local_url, body_html)

    if not body_html:
        fallback_snippet = (
            (delegate_item.snippet if delegate_item and delegate_item.snippet else None)
            or (inbox_item.snippet if inbox_item and inbox_item.snippet else None)
            or "Email content is stored locally (no HTML body was provided by the sender)."
        )
        body_html = f"<p>{fallback_snippet}</p>"

    # 3b. Backfill attachments for older Direct Emails that have a real Graph ID but no local CrmEmailAttachment rows yet
    if direct_item and not (inbox_item or delegate_item):
        if (
            email_id
            and not str(email_id).startswith(('DIRECT-', 'MANUAL_', 'DIRECT_', 'CRM-UNITY-'))
            and not CrmEmailAttachment.objects.filter(email_id=email_id).exists()
        ):
            try:
                from .management.commands.sync_outlook_emails import download_and_link_attachments
                download_and_link_attachments(email_id, body_html, received_dt=direct_item.sent_at)
            except Exception as e:
                logger.warning(f"Direct email attachment backfill skipped for {email_id}: {e}")

    # 4. Load non-inline incoming/direct attachments (excluding 'local_reply_' attachments)
    local_atts = (
        CrmEmailAttachment.objects
        .filter(email_id=email_id, is_inline=False)
        .exclude(attachment_id__startswith='local_reply_')
        .order_by('id')
    )
    attachments_list = []
    for att in local_atts:
        attachments_list.append({
            'id': att.attachment_id or str(att.id),
            'local_pk': att.id,
            'name': att.name,
            'contentType': att.content_type or 'application/octet-stream',
            'size': att.size,
            'local_url': reverse('serve_local_attachment', kwargs={'att_pk': att.id}),
        })

    return inbox_item, delegate_item, direct_item, body_html, attachments_list


def _build_local_reply_thread_html(email_id, inbox_item=None, delegate_item=None):
    """Builds the quoted original email history strictly from local database fields (zero Graph calls)."""
    source_obj = delegate_item or inbox_item or CrmInbox.objects.filter(email_id=email_id).first() or CrmDelegateTo.objects.filter(email_id=email_id).first()
    if not source_obj:
        return ""

    sender_address = getattr(source_obj, 'sender', 'Unknown') or 'Unknown'
    sender_name = getattr(source_obj, 'sender_name', '') or sender_address
    rec_dt = getattr(source_obj, 'received_timestamp', None)
    sent_date = timezone.localtime(rec_dt).strftime('%d %B %Y %H:%M') if rec_dt else 'Unknown'
    to_addresses = getattr(source_obj, 'to_recipients', '') or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', '')
    cc_addresses = getattr(source_obj, 'cc_recipients', '') or ''
    orig_subject = getattr(source_obj, 'subject', '') or ''
    orig_body = getattr(source_obj, 'body_html', '') or getattr(source_obj, 'snippet', '') or ''

    cc_line = f"<b>Cc:</b> {cc_addresses}<br>" if cc_addresses else ""

    return f"""
    <br>
    <div style="border:none; border-top:solid #B5C4DF 1.0pt; padding:3.0pt 0cm 0cm 0cm">
        <p style="margin:0cm; margin-bottom:.0001pt; font-size:11.0pt; font-family:'Calibri',sans-serif">
            <b>From:</b> {sender_name} &lt;{sender_address}&gt;<br>
            <b>Sent:</b> {sent_date}<br>
            <b>To:</b> {to_addresses}<br>
            {cc_line}
            <b>Subject:</b> {orig_subject}
        </p>
    </div>
    <br>
    {orig_body}
    """

@login_required
def dashboard(request):
    """Displays the CRM dashboard with notification badges for all users."""
    username = request.user.username

    # Exclude any email_id that already exists in CrmDelegateTo so the badge count always matches Live Inbox
    already_delegated_ids = CrmDelegateTo.objects.values_list('email_id', flat=True)
    new_emails_count = (
        CrmInbox.objects
        .filter(status='Pending')
        .exclude(email_id__in=already_delegated_ids)
        .count()
    )

    # Recycle Bin
    recycled_count = CrmDelegateTo.objects.filter(status='Recycled').count()

    # Agent Logic: My Assigned Tasks
    my_pending_tasks_count = CrmDelegateTo.objects.filter(
        delegated_to=request.user.username,
        status='Delegated'
    ).count()

    context = {
        'username': username,
        'new_emails_count': new_emails_count,               # For 'CRM_Delegations' button
        'my_pending_delegations_count': my_pending_tasks_count, # For 'Dashboard' button
        'recycled_count': recycled_count,                   # For 'Recycle Bin' button
    }
    return render(request, 'dashboard.html', context)

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')

# ==============================================================================
# MICROSOFT GRAPH EMAIL (UNITY_INTERNAL AUTOMATIC LOGIC)'delegation_timestamp': 
# ==============================================================================

@login_required
def fetch_emails_view(request):
    """
    Loads instantly from the local database.
    When ?sync=true is passed, uses Graph ONLY to check for new emails and fully download them locally.
    Strictly excludes any email that already exists in CrmDelegateTo so delegated emails never reappear.
    """
    if request.user.username.lower() != 'omega' and not request.user.is_superuser:
        messages.error(request, "Access restricted.")
        return redirect('tasks')

    # Always get the master set of already-delegated/recycled/completed email IDs
    already_delegated_ids = set(
        CrmDelegateTo.objects.values_list('email_id', flat=True)
    )

    # Self-heal any CrmInbox row that is still marked 'Pending' despite already being in CrmDelegateTo
    if already_delegated_ids:
        CrmInbox.objects.filter(
            email_id__in=already_delegated_ids,
            status='Pending'
        ).update(status='Delegated')

    if request.GET.get('sync') == 'true':
        inbox_data = OutlookGraphService.fetch_inbox_messages(top_count=100)
        if isinstance(inbox_data, dict) and 'error' not in inbox_data:
            emails = inbox_data.get('value', [])
            fully_synced_ids = set(
                CrmInbox.objects.filter(is_fully_synced=True).values_list('email_id', flat=True)
            )
            synced_count = 0
            for msg in emails:
                email_id = msg.get('id')
                # Never re-ingest as a new pending email if it's already synced or already delegated
                if email_id and email_id not in fully_synced_ids and email_id not in already_delegated_ids:
                    if ingest_single_email_from_graph(msg):
                        synced_count += 1
            messages.success(request, f"Inbox synchronized ({synced_count} new emails downloaded locally).")
        else:
            err = inbox_data.get('error', 'Unknown error') if isinstance(inbox_data, dict) else 'Connection error'
            messages.warning(request, f"Showing local emails. Outlook sync notice: {err}")
        return redirect('fetch_emails')

    # Strictly filter to Pending emails AND exclude any email_id present in CrmDelegateTo
    display_emails = (
        CrmInbox.objects
        .filter(status='Pending')
        .exclude(email_id__in=already_delegated_ids)
        .order_by('-received_timestamp')
    )
    for email in display_emails:
        email.received_at = email.received_timestamp

    paginator = Paginator(display_emails, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inbox.html', {
        'email_list': page_obj,
        'total_pending': display_emails.count()
    })


@login_required
@xframe_options_exempt
def get_email_content_view(request, email_id):
    """
    Renders the HTML email content 100% from the local database.
    Never deletes local records if an email was moved or deleted in Outlook.
    """
    _, _, _, content, _ = _ensure_local_email_data(email_id)
    wrapped_content = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body style='font-family: sans-serif;'>{content}</body></html>"
    return HttpResponse(wrapped_content, content_type='text/html')



@login_required
def delegate_email_view(request, email_id):
    """
    Handles classification and delegation for CRM_UNITY using locally stored email & attachment data.
    - 'Assign Task' (new delegation) redirects to inbox.html ('fetch_emails' -> /emails/).
    - 'Update Assignment' (re-delegating an existing task) redirects to email_workflow_log.html ('email_workflow_log').
    """
    inbox_item = get_object_or_404(CrmInbox, email_id=email_id)
    existing_delegation = CrmDelegateTo.objects.filter(email_id=email_id).first()
    is_manager = request.user.groups.filter(name='Managers').exists() or request.user.is_superuser

    if existing_delegation and not is_manager:
        messages.info(request, f"This item is already assigned to {existing_delegation.delegated_to}.")
        return redirect('tasks')

    available_agents = User.objects.filter(is_active=True)

    if request.method == 'POST':
        is_redelegation = existing_delegation is not None
        agent_name = request.POST.get('agent_name')
        work_related = request.POST.get('work_related')
        member_code = request.POST.get('mip_number')
        membership_num = request.POST.get('membership_number')

        form_data = {
            'member_group_code': member_code,
            'membership_number': membership_num,
            'category': request.POST.get('email_category'),
            'work_related': work_related,
            'type': request.POST.get('email_type'),
        }

        if work_related == 'No':
            success, message = delegate_email_task(email_id, None, request.user, form_data, is_recycle=True)
            if success:
                messages.info(request, "Email moved to CRM Recycle Bin (preserved locally).")
                return redirect('email_workflow_log' if is_redelegation else 'fetch_emails')
            else:
                messages.error(request, f"Error: {message}")
                return redirect('fetch_emails')
        else:
            if not agent_name or agent_name == "__Select Agent__":
                messages.error(request, "Please select an agent for work-related tasks.")
            else:
                success, message = delegate_email_task(email_id, agent_name, request.user, form_data)
                if success:
                    try:
                        assignee = User.objects.get(pk=agent_name) if agent_name.isdigit() else User.objects.get(username=agent_name)
                        messages.success(request, f"Task assigned to {assignee.username}. (Re-delegation: {'Yes' if is_redelegation else 'No'})")
                    except Exception:
                        messages.success(request, f"Task assigned to {agent_name}.")

                    # Redirect Update Assignment -> email_workflow_log.html, Assign Task -> inbox.html ('fetch_emails')
                    if is_redelegation:
                        return redirect('email_workflow_log')
                    return redirect('fetch_emails')

    _, _, _, email_body, attachments_list = _ensure_local_email_data(email_id)

    return render(request, 'delegate_to.html', {
        'email_id': email_id,
        'email_subject': inbox_item.subject,
        'available_agents': available_agents,
        'email_body': email_body,
        'attachments': attachments_list,
        'inbox_item': inbox_item,
        'existing_delegation': existing_delegation,
        'is_manager': is_manager
    })
    
from django.template.loader import render_to_string # Add this import to the top of your file

@login_required
def send_task_email_view(request, email_id):
    if request.method == 'POST':
        task = get_object_or_404(CrmDelegateTo, email_id=email_id)
        inbox_item = CrmInbox.objects.filter(email_id=email_id).first()

        recipient = request.POST.get('recipient_email')
        subject = request.POST.get('email_subject_reply')
        raw_message_body = request.POST.get('email_body_reply', '')

        if not raw_message_body or raw_message_body == "<p><br></p>":
            messages.error(request, "Email body cannot be empty.")
            return redirect('delegate_action', email_id=email_id)

        message_body = raw_message_body.replace('\r\n', '<br>').replace('\n', '<br>')
        logo_url = "https://static.futurasa.co.za/images/futura-logo.png"
        agent_name, agent_title = get_crm_signature_details(request.user)

        signature_html = render_to_string('email_signature.html', {
            'request': request,
            'MEDIA_URL': settings.MEDIA_URL,
            'logo_url': logo_url,
            'agent_name': agent_name,
            'agent_title': agent_title
        })

        thread_history = _build_local_reply_thread_html(email_id, inbox_item=inbox_item, delegate_item=task)
        full_message_body = f"<div>{message_body}</div><br><br>{signature_html}{thread_history}"

        response = OutlookGraphService.send_outlook_email(
            recipient_email=recipient,
            subject=subject,
            body_content=full_message_body,
            content_type='HTML'
        )

        if response.get('success'):
            CrmDelegateAction.objects.create(
                task_email_id=email_id,
                action_type='REPLY_SENT',
                action_user=request.user.username,
                note_content=full_message_body,
                body=full_message_body,
                related_subject=subject
            )

            ClientNotes.objects.create(
                related_member_group_code=task.member_group_code,
                notes=f"Email Sent (Delegated): {subject}",
                communication_type='Sent E-mail',
                action_notes='Delegation Reply',
                user=request.user.username,
                date=timezone.now()
            )
            messages.success(request, "Reply sent and logged in thread & SLA.")
        else:
            messages.error(request, f"Failed: {response.get('error')}")

        return redirect('delegate_action', email_id=email_id)

    return redirect('tasks')

# ==============================================================================
# CRM MEMBER MANAGEMENT
# ==============================================================================

@login_required
def global_members_list(request):
    # 1. Fetch base members
    members = GlobalFundContact.objects.all().order_by('member_group_code')
    
    # 2. Calculate Stats for the Banner
    total_mg_count = members.count()
    status_counts = GlobalFundContact.objects.values('fund_status').annotate(
        count=Count('fund_status')
    ).order_by('fund_status')
    
    status_summary_parts = []
    for item in status_counts:
        status_name = item['fund_status'] if item['fund_status'] else "Blank"
        status_summary_parts.append(f"{status_name} - {item['count']}")
        
    status_summary_string = "; ".join(status_summary_parts)

    # 3. Get unique statuses for the dropdown
    fund_statuses = GlobalFundContact.objects.values_list('fund_status', flat=True).distinct().order_by('fund_status')

    # 4. Get filter values
    search_query = request.GET.get('search_query')
    status_filter = request.GET.get('fund_status_filter')

    # 5. Apply Filters
    if search_query:
        members = members.filter(
            Q(member_group_code__icontains=search_query) |
            Q(member_group_name__icontains=search_query)
        )

    if status_filter and status_filter != 'all':
        members = members.filter(fund_status=status_filter)

    # 6. Fetch Related Data from separate tables
    comm_map = {c.member_group_code: c for c in CommunicationsPerson.objects.all()}
    cbc_map = {c.member_group_code: c for c in Cbc.objects.all()}

    # --- 🚀 NEW: CSV EXPORT LOGIC ---
    # If the export button was clicked, generate the CSV using the currently filtered members
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        filename = f"Global_List_{timezone.now().strftime('%Y-%m-%d')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow([
            'Group Code', 'Member Group Name', 'Fund Status',
            'Comm. Name', 'Comm. Contact', 'Comm. E-mail',
            'CBC Name', 'CBC Contact', 'CBC E-mail'
        ])

        for member in members:
            comm = comm_map.get(member.member_group_code)
            cbc = cbc_map.get(member.member_group_code)

            # Safely format related data
            comm_name = f"{comm.first_name or ''} {comm.surname or ''}".strip() if comm else "N/A"
            comm_contact = f"{comm.work_dial_code or ''} {comm.work_contact_number or 'N/A'}".strip() if comm else "N/A"
            comm_email = comm.email_address if comm and comm.email_address else "N/A"

            cbc_name = f"{cbc.first_name or ''} {cbc.surname or ''}".strip() if cbc else "N/A"
            cbc_contact = f"{cbc.work_dial_code or ''} {cbc.work_contact_number or 'N/A'}".strip() if cbc else "N/A"
            cbc_email = cbc.email_address if cbc and cbc.email_address else "N/A"

            writer.writerow([
                member.member_group_code,
                member.member_group_name,
                member.fund_status,
                comm_name,
                comm_contact,
                comm_email,
                cbc_name,
                cbc_contact,
                cbc_email
            ])
            
        return response
    # --------------------------------

    # 7. Attach data to the member objects for the template
    for member in members:
        comm = comm_map.get(member.member_group_code)
        member.comm_data = comm
        if comm:
            member.comm_full_name = f"{comm.first_name or ''} {comm.surname or ''}".strip()
        else:
            member.comm_full_name = "N/A"

        member.cbc_data = cbc_map.get(member.member_group_code)

    context = {
        'members': members,
        'fund_statuses': fund_statuses,
        'search_query': search_query,
        'fund_status_filter': status_filter,
        'total_mg_count': total_mg_count,           
        'status_summary': status_summary_string,    
    }

    return render(request, 'global_members_list.html', context)

# --- ADDED TO RELATED FORMS ---
RELATED_FORMS = [
    ('cbc_form', CbcForm, Cbc), 
    ('cbc_admin_form', CbcAdminPersonForm, CbcAdminPerson),
    ('cbc_consultancy_form', CbcConsultancyPersonForm, CbcConsultancyPerson),
    ('cfa_form', CfaForm, Cfa), 
    ('cfa_admin_form', CfaAdminPersonForm, CfaAdminPerson),
    ('cfa2_form', Cfa2Form, Cfa2), 
    ('cfa3_form', Cfa3Form, Cfa3),
    ('communications_form', CommunicationsPersonForm, CommunicationsPerson),
    ('hr_form', HumanResourcesForm, HumanResources), 
    ('section13a_form', Section13aForm, Section13a),
    ('medical_form', MedicalCorrespondenceForm, MedicalCorrespondence), # 🟢 Added Medical Form
]

from django.core.mail import EmailMessage
import urllib.parse 
import os

@login_required

@login_required

@login_required
def member_information(request, member_group_code):
    contact_info = get_object_or_404(GlobalFundContact, member_group_code=member_group_code)
    
    # --- 0. HANDLE FILE DOWNLOADS ---
    
    # Standard Email Download (Supports both Original and Reply via ?action_id=...)
    if request.method == 'GET' and 'download_email_id' in request.GET:
        email_id = request.GET.get('download_email_id')
        action_id = request.GET.get('action_id')
        if email_id in ("DIRECT_SEND_SUCCESS", "MANUAL_SEND_SUCCESS"):
            messages.warning(request, "The physical .eml file for this older record is not available.")
            return redirect('member_information', member_group_code=member_group_code)
        dl_url = reverse('download_actual_email', kwargs={'email_id': email_id})
        if action_id:
            dl_url += f"?action_id={action_id}"
        return redirect(dl_url)

    # Specific Document Download by ID
    if request.method == 'GET' and 'download_id' in request.GET:
        doc_id = request.GET.get('download_id')
        document = get_object_or_404(MemberDocument, id=doc_id, related_member_group_code=member_group_code)
        if document.document_file:
            try:
                return FileResponse(document.document_file.open('rb'), as_attachment=True, filename=document.document_file.name)
            except FileNotFoundError:
                messages.error(request, "File not found on server storage.")
        else:
            messages.error(request, "Database record exists, but no file is attached.")

    # FUZZY SEARCH DOWNLOAD LOGIC FOR NOTES ATTACHMENTS
    target_param = request.GET.get('download_note_file') or request.GET.get('file')
    
    if request.method == 'GET' and target_param:
        target_filename = urllib.parse.unquote(target_param)
        
        print(f"--- DEBUG: Attempting download for: {target_filename} ---")

        # 1. Primary Search (Exact/Contains)
        document = MemberDocument.objects.filter(
            related_member_group_code=member_group_code, 
            document_file__icontains=target_filename
        ).first()
        
        # 2. Secondary Search (Fuzzy Fallback for renamed files)
        if not document and len(target_filename) > 10:
            fuzzy_prefix = target_filename[:10]
            print(f"DEBUG: Exact match failed. Trying fuzzy prefix: {fuzzy_prefix}")
            document = MemberDocument.objects.filter(
                related_member_group_code=member_group_code,
                document_file__icontains=fuzzy_prefix
            ).first()

        if document and document.document_file:
            try:
                file_path = document.document_file.path
                if os.path.exists(file_path):
                    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                    response['Content-Disposition'] = f'attachment; filename="{target_filename}"'
                    return response
                else:
                    print(f"DEBUG ERROR: Physical file missing at {file_path}")
                    messages.error(request, "Database record found, but the file is missing from server storage.")
            except Exception as e:
                messages.error(request, f"System error during file access: {str(e)}")
        else:
            db_files = list(MemberDocument.objects.filter(
                related_member_group_code=member_group_code
            ).values_list('document_file', flat=True))
            print(f"--- DATABASE TRACE for {member_group_code} ---")
            print(f"Looking for: {target_filename}")
            print(f"Files found in DB for this member: {db_files}")
            messages.error(request, f"Could not locate document record for: {target_filename}")
            
        return redirect(f"/global-members/{member_group_code}/#notes")

    # --- START OF POST LOGIC ---
    if request.method == 'POST':
        action = request.POST.get('action')
        user_display = request.user.username 
        
        if action == 'upload_pdf':
            if 'pdf_file' in request.FILES:
                uploaded_file = request.FILES['pdf_file']
                doc_title = request.POST.get('title')
                
                MemberDocument.objects.create(
                    related_member_group_code=member_group_code,
                    document_file=uploaded_file,
                    title=doc_title,
                    uploaded_by=user_display,
                    uploaded_at=timezone.now()
                )
                messages.success(request, f"Document '{doc_title}' uploaded successfully.")
            else:
                messages.error(request, "No file was selected for upload.")
            return redirect(f"/global-members/{member_group_code}/#pdf-documents")

        elif action == 'send_direct_email':
            recipient = request.POST.get('recipient_email')
            subject = request.POST.get('subject')
            body_content = request.POST.get('email_body_html_content')
            attachments = request.FILES.getlist('attachments')
            action_log_type = request.POST.get('action_notes_email', 'Direct Email Sent')

            cc_recipients = request.POST.get('member_cc_email', '')
            bcc_recipients = request.POST.get('member_bcc_email', '')

            logo_url = "https://static.futurasa.co.za/images/futura-logo.png"
            agent_name, agent_title = get_crm_signature_details(request.user)

            signature_html = render_to_string('email_signature.html', {
                'request': request,
                'MEDIA_URL': settings.MEDIA_URL,
                'logo_url': logo_url,
                'agent_name': agent_name,
                'agent_title': agent_title
            })
            
            full_body_content = f"<div>{body_content}</div><br>{signature_html}"

            response = OutlookGraphService.send_outlook_email(
                target_email=settings.OUTLOOK_EMAIL_ADDRESS,
                recipient_email=recipient,
                subject=subject,
                body_content=full_body_content,
                content_type='HTML',
                attachments=attachments,
                cc_email=cc_recipients,
                bcc_email=bcc_recipients
            )

            if response.get('success'):
                real_outlook_id = response.get('id') or f"DIRECT-{int(timezone.now().timestamp())}"
                
                DirectEmailLog.objects.create(
                    member_group_code=member_group_code,
                    subject=subject,
                    recipient_email=recipient,
                    cc_recipients=cc_recipients,
                    bcc_recipients=bcc_recipients,
                    body_content=full_body_content,
                    sent_by_user=request.user,
                    outlook_message_id=real_outlook_id, 
                    sent_at=timezone.now(),
                    action_type=action_log_type
                )

                # Save uploaded Direct Email attachments to local disk and CrmEmailAttachment
                if attachments:
                    from .management.commands.sync_outlook_emails import _get_email_storage_dir
                    from django.utils.text import get_valid_filename
                    rel_dir, _ = _get_email_storage_dir(real_outlook_id)
                    for idx, uf in enumerate(attachments, start=1):
                        safe_uf = get_valid_filename(uf.name) or f"attachment_{idx}"
                        rel_p = os.path.join(rel_dir, f"direct_{idx}_{safe_uf}").replace('\\', '/')
                        abs_p = os.path.join(settings.MEDIA_ROOT, rel_p)
                        uf.seek(0)
                        with open(abs_p, 'wb') as out_f:
                            for chunk in uf.chunks():
                                out_f.write(chunk)
                        CrmEmailAttachment.objects.create(
                            email_id=real_outlook_id,
                            attachment_id=f"local_direct_{int(timezone.now().timestamp())}_{idx}_{safe_uf}",
                            name=uf.name,
                            content_type=getattr(uf, 'content_type', 'application/octet-stream'),
                            size=uf.size,
                            is_inline=False,
                            file_path=rel_p
                        )
                
                att_names = ", ".join([f.name for f in attachments]) if attachments else "None"
                sent_now = timezone.localtime(timezone.now()) if timezone.is_aware(timezone.now()) else timezone.now()
                note_summary = (
                    f"To: {recipient}\n"
                    f"CC: {cc_recipients or '-'}\n"
                    f"BCC: {bcc_recipients or '-'}\n"
                    f"Subject: {subject}\n"
                    f"Date & Time Sent: {sent_now.strftime('%Y-%m-%d %H:%M')}\n"
                    f"Attachments: {att_names}"
                )

                ClientNotes.objects.create(
                    related_member_group_code=member_group_code,
                    notes=note_summary,
                    communication_type='Sent E-mail',
                    action_notes=action_log_type,
                    user=user_display,
                    date=timezone.now()
                )
                messages.success(request, f"Email sent successfully with signature and logged as {action_log_type}.")
            else:
                messages.error(request, f"Microsoft Error: {response.get('error')}")
            return redirect(f"/global-members/{member_group_code}/#email-log")

        elif action == 'save_member_note':
            attached_filename = None
            if 'note_file' in request.FILES:
                uploaded_file = request.FILES['note_file']
                attached_filename = uploaded_file.name 
                MemberDocument.objects.create(
                    related_member_group_code=member_group_code,
                    document_file=uploaded_file,
                    title=f"Note Attachment: {uploaded_file.name}",
                    uploaded_by=user_display,
                    uploaded_at=timezone.now()
                )

            ClientNotes.objects.create(
                related_member_group_code=member_group_code,
                notes=request.POST.get('note_content'),
                communication_type=request.POST.get('communication_type'),
                action_notes=request.POST.get('action_notes'),
                attached_file_name=attached_filename, 
                user=user_display, 
                date=timezone.now()
            )
            messages.success(request, 'Note saved.')
            return redirect(f"/global-members/{member_group_code}/#notes")

        return redirect('member_information', member_group_code=member_group_code)

    # --- DATA RETRIEVAL ---
    personnel_data = {
        'cbc_info': Cbc.objects.filter(member_group_code=member_group_code).first(),
        'cbc_admin_info': CbcAdminPerson.objects.filter(member_group_code=member_group_code).first(),
        'cbc_consultancy_info': CbcConsultancyPerson.objects.filter(member_group_code=member_group_code).first(),
        'cfa_info': Cfa.objects.filter(member_group_code=member_group_code).first(),
        'cfa_admin_info': CfaAdminPerson.objects.filter(member_group_code=member_group_code).first(),
        'cfa2_info': Cfa2.objects.filter(member_group_code=member_group_code).first(),
        'cfa3_info': Cfa3.objects.filter(member_group_code=member_group_code).first(),
        'communications_info': CommunicationsPerson.objects.filter(member_group_code=member_group_code).first(),
        'hr_info': HumanResources.objects.filter(member_group_code=member_group_code).first(),
        'section13a_info': Section13a.objects.filter(member_group_code=member_group_code).first(),
        'medical_info': MedicalCorrespondence.objects.filter(member_group_code=member_group_code).first(),
    }

    combined_email_log = []
    # Order original delegated emails newest-first, then group each original's replies right underneath it chronologically
    delegated_items = CrmDelegateTo.objects.filter(member_group_code=member_group_code).order_by('-received_timestamp')
    related_email_ids = [item.email_id for item in delegated_items]
    inbox_records = CrmInbox.objects.filter(email_id__in=related_email_ids)
    inbox_map = {email.email_id: email.received_timestamp for email in inbox_records}

    # Pre-fetch all replies for these threads ordered chronologically (oldest reply to newest reply under its parent)
    threaded_replies = CrmDelegateAction.objects.filter(
        task_email_id__in=related_email_ids,
        action_type='REPLY_SENT'
    ).order_by('action_timestamp')

    replies_by_parent = {}
    for reply in threaded_replies:
        replies_by_parent.setdefault(reply.task_email_id, []).append(reply)

    # Pre-fetch completion timestamps for completed original tasks
    completion_actions = CrmDelegateAction.objects.filter(
        task_email_id__in=related_email_ids,
        action_type='complete'
    ).order_by('action_timestamp')
    completion_map = {act.task_email_id: act.action_timestamp for act in completion_actions}

    for item in delegated_items:
        # 1. Append the ORIGINAL incoming email first
        combined_email_log.append({
            'timestamp': item.received_timestamp,
            'arrival_timestamp': inbox_map.get(item.email_id) or item.received_timestamp,
            'delegation_timestamp': item.received_timestamp,
            'actioned_timestamp': completion_map.get(item.email_id) or item.received_timestamp if item.status == 'Completed' else None,
            'type': 'Original',
            'subject': item.subject,
            'assigned_to': item.delegated_to,
            'status': item.status,
            'email_id': item.email_id,
            'action_id': None,
            'action_user': item.delegated_by
        })

        # 2. Immediately append all REPLIES belonging to this original email in chronological order
        for reply in replies_by_parent.get(item.email_id, []):
            combined_email_log.append({
                'timestamp': reply.action_timestamp,
                'arrival_timestamp': None,
                'delegation_timestamp': None,
                'actioned_timestamp': reply.action_timestamp,
                'type': 'Reply',
                'subject': reply.related_subject or f"RE: {item.subject}",
                'assigned_to': reply.action_user,
                'status': 'Sent',
                'email_id': reply.task_email_id,
                'action_id': reply.id,
                'action_user': reply.action_user
            })

    import re
    notes = list(ClientNotes.objects.filter(related_member_group_code=member_group_code).order_by('-date'))
    for n in notes:
        if n.communication_type == 'Sent E-mail' and n.notes and ('<' in n.notes):
            # Strip any legacy HTML body appended after the Attachments: line on older notes
            n.notes = re.sub(r'(Attachments:[^\n<]*)\s*<.*', r'\1', n.notes, flags=re.DOTALL).strip()
    direct_emails = DirectEmailLog.objects.filter(member_group_code=member_group_code).order_by('-sent_at')
    documents = MemberDocument.objects.filter(related_member_group_code=member_group_code).order_by('-uploaded_at')

    context = {
        'contact_info': contact_info,
        **personnel_data,
        'notes': notes,
        'documents': documents,
        'combined_email_log': combined_email_log, 
        'direct_emails': direct_emails,
    }

    return render(request, 'member_information.html', context)

@login_required
def add_member(request):
    if request.method == 'POST':
        member_form = GlobalFundContactForm(request.POST)
        related_forms = {name: cls(request.POST) for name, cls, _ in RELATED_FORMS}
        if member_form.is_valid():
            try:
                with transaction.atomic():
                    new_mem = member_form.save()
                    code = new_mem.member_group_code
                    if 'save_all' in request.POST:
                        for name, _, model_cls in RELATED_FORMS:
                            inst = related_forms[name].save(commit=False)
                            inst.member_group_code = code
                            inst.save()
                    messages.success(request, f"Member {code} created.")
                    return redirect('member_information', member_group_code=code)
            except Exception as e:
                messages.error(request, f"Error: {e}")
    else:
        member_form = GlobalFundContactForm()
        related_forms = {name: cls() for name, cls, _ in RELATED_FORMS}
    return render(request, 'add_member.html', {'member_form': member_form, **related_forms})

# ==============================================================================
# EXCEL IMPORT (RESTORED)
# ==============================================================================


@login_required
def import_global_data(request):
    import datetime
    import zipfile
    import openpyxl
    from django.db import transaction

    if request.method == 'POST' and 'master_file' in request.FILES:
        master_file = request.FILES['master_file']
        has_header = 'header_row' in request.POST

        stats = {
            'total_created': 0,
            'total_updated': 0,
            'sheets_processed': 0,
            'errors': []
        }

        if not master_file.name.lower().endswith('.xlsx'):
            return render(request, 'import_global_data.html', {'error_message': "Only '.xlsx' files are supported."})

        if not zipfile.is_zipfile(master_file):
            return render(request, 'import_global_data.html', {'error_message': "File Structure Error."})

        def clean_val(val, is_date=False):
            if val is None:
                return None
            if is_date:
                if isinstance(val, datetime.datetime):
                    return val.date()
                if isinstance(val, datetime.date):
                    return val
                val_str = str(val).strip()
                if not val_str or val_str.lower() in ('<none>', 'none', 'null', 'nan'):
                    return None
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d.%m.%Y', '%Y/%m/%d'):
                    try:
                        return datetime.datetime.strptime(val_str[:10], fmt).date()
                    except ValueError:
                        continue
                return None
            val_str = str(val).strip()
            if val_str == '' or val_str.lower() in ('<none>', 'none', 'null', 'nan'):
                return None
            if val_str.endswith('.0') and val_str[:-2].isdigit():
                val_str = val_str[:-2]
            return val_str

        try:
            master_file.seek(0)
            # 🟢 FIX: Added read_only=True to prevent memory spikes on large files
            workbook = openpyxl.load_workbook(master_file, data_only=True, read_only=True)

            # =========================================================================
            # MODE 1: Single Horizontal Master Sheet ('Global Funds')
            # =========================================================================
            if 'Global Funds' in workbook.sheetnames:
                sheet = workbook['Global Funds']
                stats['sheets_processed'] += 1
                
                # 🟢 FIX: Stream rows as an iterator instead of loading into a list
                row_iterator = sheet.iter_rows(values_only=True)
                
                if has_header:
                    next(row_iterator, None)  # Skip the header row efficiently

                CONTACT_10 = [
                    'title', 'first_name', 'surname', 'id_number', 'email_address',
                    'work_dial_code', 'work_contact_number', 'fax_dial_code', 'fax_number', 'mobile_number'
                ]
                CONTACT_11_IND = CONTACT_10 + ['indemnity']
                CONTACT_14_ADDR = CONTACT_10 + [
                    'business_postal_address', 'post_code', 'business_physical_address', 'post_code2'
                ]
                CONTACT_15_IND_ADDR = CONTACT_11_IND + [
                    'business_postal_address', 'post_code', 'business_physical_address', 'post_code2'
                ]

                HORIZONTAL_BLOCKS = [
                    (CommunicationsPerson, 8, CONTACT_10),
                    (HumanResources, 18, CONTACT_11_IND),
                    (Section13a, 29, CONTACT_11_IND),
                    (Cbc, 40, CONTACT_15_IND_ADDR),
                    (CbcAdminPerson, 55, CONTACT_10),
                    (CbcConsultancyPerson, 65, CONTACT_10),
                    (Cfa, 75, CONTACT_14_ADDR),
                    (Cfa2, 89, CONTACT_14_ADDR),
                    (Cfa3, 103, CONTACT_14_ADDR),
                    (CfaAdminPerson, 117, CONTACT_10),
                    (MedicalCorrespondence, 127, CONTACT_10),
                ]

                # Pre-fetch existing primary keys to bulk determine created vs updated
                existing_codes = {model: set(model.objects.values_list('pk', flat=True)) 
                                  for model, _, _ in HORIZONTAL_BLOCKS}
                existing_codes[GlobalFundContact] = set(GlobalFundContact.objects.values_list('pk', flat=True))

                bulk_lists = {model: {'creates': [], 'updates': []} for model, _, _ in HORIZONTAL_BLOCKS}
                global_fund_creates = []
                global_fund_updates = []

                # Iterate one row at a time from the stream
                for row_idx, row in enumerate(row_iterator, start=2 if has_header else 1):
                    if not row or len(row) < 8:
                        continue

                    mg_code = clean_val(row[0])
                    if not mg_code:
                        continue

                    # 1. Core GlobalFundContact
                    fund_defaults = {
                        'member_group_name': clean_val(row[1]),
                        'commencement_date': clean_val(row[2], is_date=True),
                        'fund_status': clean_val(row[3]),
                        'business_postal_address': clean_val(row[4]),
                        'business_postal_address_post_code': clean_val(row[5]),
                        'business_physical_address2': clean_val(row[6]),
                        'business_physical_address_post_code2': clean_val(row[7]),
                    }
                    fund_clean = {k: v for k, v in fund_defaults.items() if v is not None}

                    if mg_code in existing_codes[GlobalFundContact]:
                        GlobalFundContact.objects.filter(pk=mg_code).update(**fund_clean)
                        stats['total_updated'] += 1
                    else:
                        obj = GlobalFundContact(member_group_code=mg_code, **fund_clean)
                        global_fund_creates.append(obj)
                        existing_codes[GlobalFundContact].add(mg_code)
                        stats['total_created'] += 1

                    # 2. Contact Models
                    for model_cls, col_start, field_names in HORIZONTAL_BLOCKS:
                        block_data = {}
                        for offset, field_name in enumerate(field_names):
                            col_pos = col_start + offset
                            if col_pos < len(row):
                                val = clean_val(row[col_pos])
                                if val is not None:
                                    if field_name in ('work_dial_code', 'fax_dial_code', 'post_code', 'post_code2'):
                                        val = val[:10]
                                    block_data[field_name] = val

                        if block_data:
                            if mg_code in existing_codes[model_cls]:
                                model_cls.objects.filter(pk=mg_code).update(**block_data)
                                stats['total_updated'] += 1
                            else:
                                obj = model_cls(member_group_code=mg_code, **block_data)
                                bulk_lists[model_cls]['creates'].append(obj)
                                existing_codes[model_cls].add(mg_code)
                                stats['total_created'] += 1

                # Execute bulk creates efficiently inside a single transaction
                with transaction.atomic():
                    if global_fund_creates:
                        GlobalFundContact.objects.bulk_create(global_fund_creates, batch_size=500)
                    for model_cls, data in bulk_lists.items():
                        if data['creates']:
                            model_cls.objects.bulk_create(data['creates'], batch_size=500)

            # =========================================================================
            # MODE 2: Legacy Multi-Sheet Format
            # =========================================================================
            else:
                sheet_model_map = {
                    'global_fund_contact_list': GlobalFundContact,
                    'cbc': Cbc,
                    'cbc_admin_person': CbcAdminPerson,
                    'cbc_consultancy_person': CbcConsultancyPerson,
                    'cfa': Cfa,
                    'cfa_admin_person': CfaAdminPerson,
                    'cfa2': Cfa2,
                    'cfa3': Cfa3,
                    'communications_person': CommunicationsPerson,
                    'human_resources': HumanResources,
                    'section13a': Section13a,
                    'section_13a': Section13a,
                    'medical_correspondence': MedicalCorrespondence,
                }

                HEADER_ALIASES = {
                    'e-mail_address': 'email_address',
                    'e_mail_address': 'email_address',
                    'email': 'email_address',
                    'business_physical_address': 'business_physical_address2',
                    'business_physical_address_post_code': 'business_physical_address_post_code2',
                }

                for sheet_name in workbook.sheetnames:
                    norm_sheet = sheet_name.strip().lower().replace(' ', '_')
                    model_class = sheet_model_map.get(norm_sheet)
                    if not model_class:
                        continue

                    sheet = workbook[sheet_name]
                    stats['sheets_processed'] += 1
                    
                    # 🟢 FIX: Iterator for legacy sheets too
                    row_iterator = sheet.iter_rows(values_only=True)
                    header_row = next(row_iterator, None)
                    
                    if not header_row:
                        continue

                    valid_fields = {f.name for f in model_class._meta.get_fields()}
                    header = []
                    for cell_val in header_row:
                        if cell_val:
                            h = str(cell_val).strip().lower().replace(' ', '_')
                            h = HEADER_ALIASES.get(h, h)
                            header.append(h)
                        else:
                            header.append(None)

                    for row_idx, row in enumerate(row_iterator, start=2):
                        row_data = dict(zip(header, row))
                        mg_code = clean_val(
                            row_data.pop('member_group_code', None) or
                            row_data.pop('group_code', None) or
                            row_data.pop('code', None)
                        )
                        if not mg_code:
                            continue

                        clean_data = {}
                        for k, v in row_data.items():
                            if k and k in valid_fields:
                                cleaned = clean_val(v, is_date=(k == 'commencement_date'))
                                if cleaned is not None:
                                    clean_data[k] = cleaned

                        try:
                            with transaction.atomic():
                                _, created = model_class.objects.update_or_create(
                                    member_group_code=mg_code,
                                    defaults=clean_data
                                )
                                if created:
                                    stats['total_created'] += 1
                                else:
                                    stats['total_updated'] += 1
                        except Exception as e:
                            stats['errors'].append(f"Sheet '{sheet_name}', Row {row_idx} (Code: {mg_code}): {str(e)}")

            # Always clean up the workbook memory safely when done
            workbook.close()

            if stats['sheets_processed'] == 0:
                return render(request, 'import_global_data.html', {
                    'error_message': f"No matching sheets found. Workbook tabs: {', '.join(workbook.sheetnames)}"
                })

            summary_msg = (
                f"Successfully processed {stats['sheets_processed']} sheet(s). "
                f"{stats['total_updated']} records updated, "
                f"{stats['total_created']} records created."
            )
            return render(request, 'import_global_data.html', {
                'success_message': summary_msg,
                'import_errors': stats['errors']
            })

        except Exception as e:
            return render(request, 'import_global_data.html', {'error_message': f"Critical failure: {str(e)}"})

    return render(request, 'import_global_data.html')

# ==============================================================================
# AGENT WORKFLOW & REPORTS
# ==============================================================================

@login_required
def tasks_view(request):
    """
    EMAIL DASHBOARD: 
    Manager (omega) sees ALL delegated tasks (Delegated AND Completed).
    Agents see ONLY tasks assigned to them.
    """
    CATEGORY_CHOICES = {
        '0': '0. No Action Required',
        '1': '1. Reconciliation',
        '2': '2. Claim',
        '3': '3. Section 13A',
        '4': '4. New Business',
        '5': '5. Amendments',
        '6': '6. Section 28',
        '7': '7. Section 14',
        '8': '8. Section 27',
        '9': '9. Complaints',
        '10': '10. Two Pot',
        '11': '11. Report Back',
        '12': '12. Broker Investigations',
        '13': '13. General',
        '14': '14. Other'
    }

    VISIBLE_STATUSES = ['Delegated', 'Completed']

    if request.user.username.lower() == 'omega':
        tasks_qs = CrmDelegateTo.objects.filter(status__in=VISIBLE_STATUSES).order_by('-received_timestamp')
    else:
        tasks_qs = CrmDelegateTo.objects.filter(
            delegated_to=request.user.username, 
            status__in=VISIBLE_STATUSES
        ).order_by('-received_timestamp')
    
    related_email_ids = [t.email_id for t in tasks_qs]
    inbox_records = CrmInbox.objects.filter(email_id__in=related_email_ids)
    inbox_map = {email.email_id: email for email in inbox_records}

    display_tasks = []
    for t in tasks_qs:
        inbox_item = inbox_map.get(t.email_id)
        raw_cat = str(t.category).strip() if t.category else ""
        display_category = CATEGORY_CHOICES.get(raw_cat, t.category)
        
        display_tasks.append({
            'subject': t.subject,
            'email_id': t.email_id,
            'member_group_code': t.member_group_code,
            'arrival_timestamp': inbox_item.received_timestamp if inbox_item else None,
            'sender': inbox_item.sender if inbox_item else "Unknown Sender",
            'delegation_timestamp': t.received_timestamp,
            'category': display_category,
            'enquiry_type': t.type, 
            'status': t.status,
            'delegated_to': t.delegated_to
        })

    return render(request, 'tasks.html', {'delegated_tasks': display_tasks})

@login_required
def delegate_action_view(request, email_id):
    """
    Detailed view for a specific task in CRM_UNITY (100% locally rendered).
    Captures 'source' to handle conditional 'Back' button logic.
    Supports multi-file output arrays for delegated reply updates.
    """
    task = get_object_or_404(CrmDelegateTo, email_id=email_id)
    target_email = settings.OUTLOOK_EMAIL_ADDRESS

    source = request.GET.get('from')
    action_history = CrmDelegateAction.objects.filter(task_email_id=email_id).order_by('-action_timestamp')

    # Render email body and attachments 100% from local DB and disk
    inbox_item, delegate_item, _, email_body, attachments_list = _ensure_local_email_data(email_id)
    if delegate_item:
        task = delegate_item

    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        user_display = request.user.username

        with transaction.atomic():
            if action_type == 'restore_to_inbox':
                restore_note = request.POST.get('restore_note', 'Restored from Recycle Bin to Main Inbox.')
                is_from_recycle_bin = (task.status == 'Recycled')

                try:
                    inbox_obj = CrmInbox.objects.get(email_id=email_id)
                    inbox_obj.status = 'Pending'
                    inbox_obj.delegated_to = None
                    inbox_obj.save()
                except CrmInbox.DoesNotExist:
                    pass

                CrmDelegateAction.objects.create(
                    task_email_id=email_id,
                    action_type='restore_to_inbox',
                    action_user=user_display,
                    note_content=restore_note
                )

                task.delete()
                messages.success(request, "Task successfully moved back to the original Inbox queue.")

                if is_from_recycle_bin:
                    return redirect('recycle_bin')
                return redirect('fetch_emails')

            elif action_type == 'update_metadata':
                form_mip = request.POST.get('mip_number')
                task.member_group_code = form_mip
                task.membership_number = request.POST.get('membership_number')
                task.id_passport = request.POST.get('id_passport')
                task.category = request.POST.get('email_category')
                task.type = request.POST.get('email_type')
                task.method = request.POST.get('email_method') or task.method or 'Email'
                task.save()

                if inbox_item:
                    inbox_item.member_group_code = form_mip
                    inbox_item.id_passport = task.id_passport
                    inbox_item.category = task.category
                    inbox_item.type = task.type
                    inbox_item.save()

                CrmDelegateAction.objects.create(
                    task_email_id=email_id,
                    action_type='update_metadata',
                    action_user=user_display,
                    note_content=f"Updated metadata: Member Group Code {form_mip}"
                )
                messages.success(request, "Task metadata updated successfully.")

            elif action_type == 'add_note':
                note_text = request.POST.get('internal_note')
                comm_type = request.POST.get('communication_type')
                action_note_val = request.POST.get('action_notes_email')

                current_notes_raw = task.internal_notes

                if not current_notes_raw or current_notes_raw == "":
                    current_notes = []
                else:
                    try:
                        current_notes = json.loads(current_notes_raw)
                    except json.JSONDecodeError:
                        current_notes = [{"user": "System", "note": current_notes_raw, "timestamp": ""}]

                new_note_entry = {
                    'user': user_display,
                    'note': f"[{comm_type} - {action_note_val}] {note_text}",
                    'timestamp': timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                current_notes.append(new_note_entry)

                task.internal_notes = json.dumps(current_notes)
                task.save()

                ClientNotes.objects.create(
                    related_member_group_code=task.member_group_code,
                    notes=note_text,
                    communication_type=f"Delegated: {comm_type}",
                    action_notes=action_note_val,
                    user=user_display,
                    date=timezone.now()
                )

                CrmDelegateAction.objects.create(
                    task_email_id=email_id,
                    action_type='add_note',
                    action_user=user_display,
                    note_content=note_text
                )
                messages.success(request, "Internal note saved and logged to SLA.")

            elif action_type == 'complete':
                final_note = request.POST.get('completion_notes', 'Task completed.')
                task.status = 'Completed'
                task.save()

                ClientNotes.objects.create(
                    related_member_group_code=task.member_group_code,
                    notes=f"Task Completed: {final_note}",
                    communication_type='Delegated: Task Finalized',
                    action_notes='Delegation Closure',
                    user=user_display,
                    date=timezone.now()
                )

                CrmDelegateAction.objects.create(
                    task_email_id=email_id,
                    action_type='complete',
                    action_user=user_display,
                    note_content=final_note
                )
                messages.success(request, "Task marked as Completed.")
                return redirect('tasks')

            elif action_type == 'send_response':
                recipient = request.POST.get('recipient')
                subject = request.POST.get('subject')
                raw_body_html = request.POST.get('email_html_content', '')
                action_log_type = request.POST.get('action_log_type', 'General Feedback')

                cc_recipients = request.POST.get('member_cc_email', '')
                bcc_recipients = request.POST.get('member_bcc_email', '')
                uploaded_files = request.FILES.getlist('attachments')

                body_html = raw_body_html.replace('\r\n', '<br>').replace('\n', '<br>')

                if recipient and subject and body_html:
                    logo_url = "https://static.futurasa.co.za/images/futura-logo.png"
                    agent_name, agent_title = get_crm_signature_details(request.user)

                    signature_html = render_to_string('email_signature.html', {
                        'request': request,
                        'MEDIA_URL': settings.MEDIA_URL,
                        'logo_url': logo_url,
                        'agent_name': agent_name,
                        'agent_title': agent_title
                    })

                    # Build thread history strictly from local DB (no Graph call)
                    thread_history = _build_local_reply_thread_html(email_id, inbox_item=inbox_item, delegate_item=task)
                    full_body_html = f"<div>{body_html}</div><br><br>{signature_html}{thread_history}"

                    result = OutlookGraphService.send_outlook_email(
                        target_email=target_email,
                        recipient_email=recipient,
                        subject=subject,
                        body_content=full_body_html,
                        content_type='HTML',
                        attachments=uploaded_files,
                        cc_email=cc_recipients,
                        bcc_email=bcc_recipients
                    )

                    if result.get('success') or result == {}:
                        att_names = ", ".join([f.name for f in uploaded_files]) if uploaded_files else None

                        # Save uploaded reply attachments locally so they are available offline
                        saved_paths = []
                        if uploaded_files:
                            from .management.commands.sync_outlook_emails import _get_email_storage_dir
                            from django.utils.text import get_valid_filename
                            rel_dir, _ = _get_email_storage_dir(email_id)
                            for uf in uploaded_files:
                                safe_uf = get_valid_filename(uf.name)
                                rel_p = os.path.join(rel_dir, f"reply_{int(timezone.now().timestamp())}_{safe_uf}").replace('\\', '/')
                                abs_p = os.path.join(settings.MEDIA_ROOT, rel_p)
                                uf.seek(0)
                                with open(abs_p, 'wb') as out_f:
                                    for chunk in uf.chunks():
                                        out_f.write(chunk)
                                saved_paths.append(rel_p)
                                CrmEmailAttachment.objects.create(
                                    email_id=email_id,
                                    attachment_id=f"local_reply_{int(timezone.now().timestamp())}_{safe_uf}",
                                    name=uf.name,
                                    content_type=getattr(uf, 'content_type', 'application/octet-stream'),
                                    size=uf.size,
                                    is_inline=False,
                                    file_path=rel_p
                                )

                        CrmDelegateAction.objects.create(
                            task_email_id=email_id,
                            action_type='REPLY_SENT',
                            action_user=user_display,
                            note_content=f"{action_log_type} || TO:{recipient}",
                            body=full_body_html,
                            cc_recipients=cc_recipients,
                            bcc_recipients=bcc_recipients,
                            related_subject=subject,
                            attachment_name=att_names,
                            attachment_path=", ".join(saved_paths) if saved_paths else None
                        )

                        reply_now = timezone.localtime(timezone.now()) if timezone.is_aware(timezone.now()) else timezone.now()
                        note_summary = (
                            f"To: {recipient}\n"
                            f"CC: {cc_recipients or '-'}\n"
                            f"BCC: {bcc_recipients or '-'}\n"
                            f"Subject: {subject}\n"
                            f"Date & Time Replied: {reply_now.strftime('%Y-%m-%d %H:%M')}\n"
                            f"Attachments: {att_names or 'None'}"
                        )

                        ClientNotes.objects.create(
                            related_member_group_code=task.member_group_code,
                            notes=note_summary,
                            communication_type='Sent E-mail',
                            action_notes=action_log_type,
                            user=user_display,
                            date=timezone.now()
                        )
                        messages.success(request, "Reply Sent successfully.")
                    else:
                        messages.error(request, f"Email failed: {result.get('error')}")

        redirect_url = reverse('delegate_action', kwargs={'email_id': email_id})
        if source:
            redirect_url += f"?from={source}"
        return redirect(redirect_url)

    # Clean up note_content display on delegate_action.html if it contains "|| TO:"
    for act in action_history:
        if act.action_type == 'REPLY_SENT' and act.note_content and "|| TO:" in act.note_content:
            act.note_content = act.note_content.split("|| TO:", 1)[0].strip()

    return render(request, 'delegate_action.html', {
        'task': task,
        'inbox_item': inbox_item,
        'action_history': action_history,
        'email_id': email_id,
        'attachments': attachments_list,
        'source': source,
        'email_body': email_body,
    })


def _resolve_reply_recipient(reply_action, source_obj=None):
    """
    Returns (recipient_to, clean_log_type) for a REPLY_SENT CrmDelegateAction.
    Works for both newly sent replies and existing historical replies.
    """
    raw_note = (reply_action.note_content or '').strip()
    recipient_to = ""
    clean_log_type = raw_note

    # 1. Check if stored directly in note_content as "Log Type || TO:email@..."
    if "|| TO:" in raw_note:
        parts = raw_note.split("|| TO:", 1)
        clean_log_type = parts[0].strip()
        recipient_to = parts[1].strip()

    # 2. Check the matching ClientNotes entry created when this reply was sent
    if not recipient_to:
        member_code = getattr(source_obj, 'member_group_code', None)
        notes_qs = ClientNotes.objects.filter(communication_type='Sent E-mail')
        if member_code:
            notes_qs = notes_qs.filter(related_member_group_code=member_code)
        if reply_action.related_subject:
            notes_qs = notes_qs.filter(notes__icontains=f"Subject: {reply_action.related_subject}")

        for cn in notes_qs.order_by('-date')[:10]:
            for line in (cn.notes or '').splitlines():
                line_s = line.strip()
                if line_s.lower().startswith('to:'):
                    cand = line_s[3:].strip()
                    if cand:
                        recipient_to = cand
                        break
            if recipient_to:
                break

    # 3. Final fallback to original sender
    if not recipient_to and source_obj:
        recipient_to = getattr(source_obj, 'sender', '') or ''

    return recipient_to, clean_log_type

from django.db.models import Count

@login_required
def delegation_report_view(request):

    # 1. Get Date Filters
    date_query, start_date, end_date = get_date_filters(request)
    valid_entries_filter = Q(category__isnull=False) & ~Q(category='') & \
                           Q(type__isnull=False) & ~Q(type='') & ~Q(type='None')
    
    final_filter = date_query & valid_entries_filter

    # --- SECTION 1: OVERALL TOTALS ---
    all_emails_total = CrmDelegateTo.objects.filter(date_query).count()
    work_stats = CrmDelegateTo.objects.filter(date_query).values('work_related').annotate(count=Count('email_id'))
    
    work_related_data = {'Yes': 0, 'No': 0}
    for item in work_stats:
        status = item['work_related']
        if status in work_related_data:
            work_related_data[status] = item['count']

    # --- SECTION 2: BREAKDOWN & SUMMARY (Existing Logic) ---
    raw_breakdown = CrmDelegateTo.objects.filter(final_filter).values('category', 'type').annotate(count=Count('email_id')).order_by('category', 'type')
    type_selection_breakdown = []
    for item in raw_breakdown:
        type_selection_breakdown.append({
            'category': CATEGORY_NAMES.get(str(item['category']), item['category']),
            'type': item['type'],
            'grouping': ENQUIRY_GROUPING_MAP.get(item['type'], "Unmapped"),
            'count': item['count']
        })

    raw_summary = CrmDelegateTo.objects.filter(final_filter).values('category').annotate(subtotal=Count('email_id')).order_by('-subtotal')
    category_summary = []
    for item in raw_summary:
        category_summary.append({
            'category': CATEGORY_NAMES.get(str(item['category']), item['category']),
            'subtotal': item['subtotal']
        })

    # --- SECTION 4: DETAILED FLOW & SLA CALCULATION ---
    # This section feeds your new popup/modal
    detailed_records = []
    records_qs = CrmDelegateTo.objects.filter(date_query).order_by('-received_timestamp')

    for item in records_qs:
        # Get Original Arrival Time
        inbox_item = CrmInbox.objects.filter(email_id=item.email_id).first()
        received_date = inbox_item.received_timestamp if inbox_item else item.received_timestamp
        
        # Get the Manager/User who performed the action
        first_action = CrmDelegateAction.objects.filter(task_email_id=item.email_id).order_by('action_timestamp').first()
        actioned_by = first_action.action_user if first_action else "System"

        # SLA Logic: If (Delegation Date - Received Date) > 2 Days
        # Note: item.received_timestamp is the time it was delegated
        sla_flag = "Within SLA"
        if received_date:
            time_diff = item.received_timestamp - received_date
            if time_diff > timedelta(days=2):
                sla_flag = "Out of SLA"

        detailed_records.append({
            'received_date': received_date,
            'actioned_by': actioned_by,
            'action_date': item.received_timestamp,
            'delegated_to': item.delegated_to or "Unassigned",
            'member_code': item.member_group_code or "N/A",
            'sla_status': sla_flag
        })

    context = {
        'all_emails_total': all_emails_total,
        'work_related_data': work_related_data,
        'type_selection_breakdown': type_selection_breakdown,
        'category_summary': category_summary,
        'detailed_records': detailed_records, # Pass to popup
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'delegation_summary_report.html', context)

@login_required
def complaint_log_view(request):
    # --- 1. HANDLE FILTERS ---
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Helper to check for "None" strings from the URL
    def is_valid_dt(val):
        return val and val != "None" and val != ""

    # --- 2. CHECK FOR EDIT MODE ---
    edit_id = request.GET.get('edit_id')
    instance = None
    if edit_id:
        instance = get_object_or_404(ComplaintLog, pk=edit_id)

    # --- 3. INITIALIZE FORM ---
    form = ComplaintLogForm(request.POST or None, instance=instance)

    # --- 4. HANDLE POST (SAVE/UPDATE) ---
    if request.method == 'POST':
        if form.is_valid():
            comp = form.save(commit=False)
            if not instance:
                comp.created_by = request.user
            comp.save()
            
            msg = "Complaint updated successfully." if instance else "Complaint logged successfully."
            messages.success(request, msg)
            return redirect('complaint_log')

    # --- 5. DATA RETRIEVAL WITH FILTERS ---
    complaints = ComplaintLog.objects.all()

    if is_valid_dt(start_date):
        complaints = complaints.filter(created_at__date__gte=start_date)
    if is_valid_dt(end_date):
        complaints = complaints.filter(created_at__date__lte=end_date)

    complaints = complaints.order_by('-created_at')
    
    context = {
        'form': form, 
        'complaints': complaints,
        'is_editing': instance is not None,
        'title': 'Complaint Registry'
    }
    return render(request, 'complaint_log.html', context)


@login_required
def export_complaints_excel(request):
    """Exports filtered complaints to Excel, including all new fields (12.4)."""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    def is_valid_dt(val):
        return val and val != "None" and val != ""

    # Fetch base records
    complaints = ComplaintLog.objects.all()

    # Apply same filters
    if is_valid_dt(start_date):
        complaints = complaints.filter(created_at__date__gte=start_date)
    if is_valid_dt(end_date):
        complaints = complaints.filter(created_at__date__lte=end_date)

    complaints = complaints.order_by('-created_at')

    # Create Workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Complaint Log Export"

    # 12.4 - Header Styling with new fields
    headers = [
        'ID', 'Complainant', 'Member Number', 'ID/Passport', 'Employer', 
        'PFA', 'Nature of Complaint', 'Action Taken', 'Resolution',
        'Status', 'Created By', 'Created Date', 'Resolved Date'
    ]
    ws.append(headers)

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
    
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # Fill Data
    for c in complaints:
        ws.append([
            c.id,
            c.complainant,
            c.member_number or 'N/A',
            c.id_passport_number or 'N/A',
            c.employer or 'N/A',
            c.pfa or 'No',
            c.nature_of_complaint,
            c.action_taken or '',
            c.resolution or '',
            c.current_status,
            c.created_by.username if c.created_by else 'System',
            c.created_at.replace(tzinfo=None) if c.created_at else 'N/A',
            c.resolved_date.replace(tzinfo=None) if c.resolved_date else 'Pending'
        ])

    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if cell.value and len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except: pass
        ws.column_dimensions[column_letter].width = min(max_length + 2, 50) # Cap width at 50 for text fields

    # Return Excel File
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"Complaint_Log_{timezone.now().strftime('%Y-%m-%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    
    return response

from django.core.paginator import Paginator

@login_required
def email_registry_view(request):
    """
    MANAGER (omega) ONLY: Email Registry / Delegations Overview.
    Shows all emails, their statuses, and allows searching/pagination.
    """
    
    # 1. Get all delegated tasks from the database
    # We order by received_timestamp descending so newest items are on top
    all_tasks = CrmDelegateTo.objects.all().order_by('-received_timestamp')

    # 2. Setup Pagination (matching your template's page_obj variable)
    # 10 tasks per page
    paginator = Paginator(all_tasks, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'delegations_overview.html', {
        'page_obj': page_obj
    })
    
@login_required
def recycle_bin_view(request):
    """
    MANAGER (omega) ONLY: View items marked for Recycle Bin.
    Filters by the status string 'Recycled'.
    """

    # Status must match the 'final_status' variable in your service layer
    recycled_items = CrmDelegateTo.objects.filter(
        status='Recycled'
    ).order_by('-received_timestamp')

    return render(request, 'recycle_bin.html', {
        'recycled_tasks': recycled_items
    })

@login_required
def delete_recycled_tasks_view(request):
    """
    Handles the POST request from the 'Delete Selected' button.
    """
    if request.method == 'POST' and request.user.username.lower() == 'omega':
        email_ids = request.POST.getlist('email_ids')
        if email_ids:
            # Physically delete or mark as permanently purged
            count = CrmDelegateTo.objects.filter(email_id__in=email_ids).delete()
            messages.success(request, f"Successfully purged {count[0]} emails from the system.")
        else:
            messages.warning(request, "No items were selected for deletion.")
            
    return redirect('recycle_bin')

@login_required
def serve_local_attachment_view(request, att_pk):
    """Serves a locally stored attachment or inline CID image from disk."""
    att = get_object_or_404(CrmEmailAttachment, pk=att_pk)
    abs_path = os.path.join(settings.MEDIA_ROOT, att.file_path)
    if not os.path.exists(abs_path):
        raise Http404("Local attachment file not found on disk.")

    content_type = att.content_type or mimetypes.guess_type(att.name)[0] or 'application/octet-stream'
    response = FileResponse(open(abs_path, 'rb'), content_type=content_type)
    if not att.is_inline:
        response['Content-Disposition'] = f'attachment; filename="{att.name}"'
    return response


@login_required
def download_attachment_view(request, message_id, attachment_id):
    """
    Serves email attachments from local disk first.
    Falls back to streaming from Microsoft Graph only if not yet on disk.
    """
    local_att = CrmEmailAttachment.objects.filter(
        email_id=message_id
    ).filter(
        Q(attachment_id=attachment_id) | Q(id=attachment_id if str(attachment_id).isdigit() else -1)
    ).first()

    if local_att:
        abs_path = os.path.join(settings.MEDIA_ROOT, local_att.file_path)
        if os.path.exists(abs_path):
            content_type = local_att.content_type or 'application/octet-stream'
            return FileResponse(open(abs_path, 'rb'), as_attachment=True, filename=local_att.name, content_type=content_type)

    # Fallback for historic emails not yet synced to disk
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    try:
        meta_endpoint = f"messages/{message_id}/attachments/{attachment_id}?$select=name,contentType"
        meta_data = OutlookGraphService._make_graph_request(meta_endpoint, target_email=target_email, method='GET')
        if isinstance(meta_data, dict) and 'error' in meta_data:
            messages.error(request, f"Attachment unavailable locally and Outlook returned: {meta_data['error']}")
            return redirect('delegate_action', email_id=message_id)

        filename = meta_data.get('name', 'attachment') if isinstance(meta_data, dict) else 'attachment'
        content_type = meta_data.get('contentType', 'application/octet-stream') if isinstance(meta_data, dict) else 'application/octet-stream'

        file_stream = OutlookGraphService.stream_attachment_mime(target_email, message_id, attachment_id)
        if not file_stream:
            messages.error(request, "Failed to open file stream.")
            return redirect('delegate_action', email_id=message_id)

        response = StreamingHttpResponse(file_stream, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger.error(f"Attachment download failed: {str(e)}")
        messages.error(request, f"Download failed: {str(e)}")
        return redirect('delegate_action', email_id=message_id)


@login_required
def view_email_thread(request, email_id):
    """
    Renders either:
    - 'incoming' mode (when clicking View on an ORIGINAL/Incoming email): shows ONLY the incoming email & its attachments.
    - 'reply' mode (when clicking View on a REPLY row with ?action_id=<id>): shows ONLY that specific Reply Sent section.
    """
    action_id = request.GET.get('action_id')
    inbox_item, delegate_item, direct_item, email_body, attachments_list = _ensure_local_email_data(email_id)

    is_direct = bool(direct_item and not delegate_item)
    task = delegate_item or direct_item or inbox_item
    if not task:
        raise Http404("No email record found for this ID.")

    # Resolve sender, To, CC, BCC, and Received Date for the incoming email header
    sender_email = (
        getattr(inbox_item, 'sender', None)
        or getattr(delegate_item, 'sender', None)
        or getattr(direct_item, 'sender_email', None)
        or 'Unknown'
    )
    sender_name = (
        getattr(inbox_item, 'sender_name', None)
        or getattr(delegate_item, 'sender_name', None)
        or sender_email
    )
    cc_recipients = (
        getattr(inbox_item, 'cc_recipients', None)
        or getattr(delegate_item, 'cc_recipients', None)
        or getattr(direct_item, 'cc_recipients', None)
        or ''
    )
    bcc_recipients = (
        getattr(inbox_item, 'bcc_recipients', None)
        or getattr(delegate_item, 'bcc_recipients', None)
        or getattr(direct_item, 'bcc_recipients', None)
        or ''
    )

    # Map reply attachments stored locally so they can be downloaded from the Reply card
    reply_atts_qs = CrmEmailAttachment.objects.filter(
        email_id=email_id,
        attachment_id__startswith='local_reply_'
    ).order_by('id')

    if action_id and str(action_id).isdigit():
        view_mode = 'reply'
        actions = list(CrmDelegateAction.objects.filter(pk=int(action_id), task_email_id=email_id))
    else:
        view_mode = 'incoming'
        actions = list(
            CrmDelegateAction.objects
            .filter(task_email_id=email_id)
            .exclude(action_type='REPLY_SENT')
            .order_by('action_timestamp')
        )

    # Attach downloadable file objects to each REPLY_SENT action
    for act in actions:
        act.downloadable_files = []
        if act.action_type == 'REPLY_SENT' and act.attachment_name:
            names = [n.strip() for n in act.attachment_name.split(',') if n.strip()]
            for name in names:
                matched_att = next((a for a in reply_atts_qs if a.name == name), None)
                if matched_att:
                    act.downloadable_files.append({
                        'name': matched_att.name,
                        'url': reverse('serve_local_attachment', kwargs={'att_pk': matched_att.id})
                    })
                else:
                    act.downloadable_files.append({
                        'name': name,
                        'url': None
                    })

    context = {
        'task': task,
        'is_direct': is_direct,
        'inbox_item': inbox_item,
        'actions': actions,
        'email_body': email_body,
        'attachments': attachments_list,
        'email_id': email_id,
        'view_mode': view_mode,
        'action_id': action_id,
        'sender_name': sender_name,
        'sender_email': sender_email,
        'cc_recipients': cc_recipients,
        'bcc_recipients': bcc_recipients,
    }
    return render(request, 'email_thread.html', context)

@login_required
def export_delegation_report_excel(request):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from django.http import HttpResponse
    from django.utils import timezone
    from django.db.models import Q

    # 1. Apply date filters using the helper
    date_query, start_str, end_str = get_date_filters(request)
    
    # Filter for entries that have been categorized/processed
    valid_entries_filter = Q(category__isnull=False) & ~Q(category='')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Delegation Flow Report"

    # 2. HEADER DEFINITION
    headers = [
        'Communication Type',       # From ClientNotes or Default 'Email'
        'Email Received Date',      # Original Arrival from Inbox
        'Actioned By',              # The Manager/User who delegated
        'Date of Action',           # When it was delegated
        'Delegated To',             # Assigned Agent
        'Member Group Code', 
        'Main Category', 
        'Enquiry Selection', 
        'Grouping', 
        'Status'
    ]
    ws.append(headers)

    # Apply Corporate Green Styling to Header Row
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1B5E20", end_color="1B5E20", fill_type="solid")
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # 3. Fetch Email Delegation Records
    email_records = CrmDelegateTo.objects.filter(
        date_query & valid_entries_filter
    ).order_by('-received_timestamp')

    # 4. Fill Excel Rows with Email Data
    for item in email_records:
        first_action = CrmDelegateAction.objects.filter(
            task_email_id=item.email_id
        ).order_by('action_timestamp').first()
        actioned_by_user = first_action.action_user if first_action else (item.delegated_by or "System")

        inbox_record = CrmInbox.objects.filter(email_id=item.email_id).first()
        received_date = inbox_record.received_timestamp.replace(tzinfo=None) if inbox_record and inbox_record.received_timestamp else item.received_timestamp.replace(tzinfo=None)

        category_display = CATEGORY_NAMES.get(str(item.category), str(item.category)) if item.category else "Unclassified"
        grouping_display = ENQUIRY_GROUPING_MAP.get(item.type, "Unmapped") if item.type else "N/A"

        ws.append([
            "Email",                                            # Communication Type
            received_date,                                      # Email Received Date
            actioned_by_user,                                   # Actioned By
            item.received_timestamp.replace(tzinfo=None),       # Date of Action
            item.delegated_to or "Unassigned",                  # Delegated To
            item.member_group_code or "N/A",                    # Member Group Code
            category_display,                                   # Main Category
            item.type or "None",                                # Enquiry Selection
            grouping_display,                                   # Grouping
            item.status                                         # Status
        ])

    # 5. Fetch and Append Client Notes (Calls/Teams/etc)
    # --- SAFETY CHECK FOR "None" STRINGS ---
    def is_valid_date_str(val):
        return val and val != "None" and val != ""

    notes_filter = Q()
    if is_valid_date_str(start_str):
        notes_filter &= Q(date__date__gte=start_str)
    if is_valid_date_str(end_str):
        notes_filter &= Q(date__date__lte=end_str)

    note_records = ClientNotes.objects.filter(notes_filter).order_by('-date')

    for note in note_records:
        ws.append([
            note.communication_type or "Note",                  # Communication Type
            "N/A",                                              # Email Received Date
            note.user,                                          # Actioned By
            note.date.replace(tzinfo=None),                     # Date of Action
            "N/A",                                              # Delegated To
            note.related_member_group_code or "N/A",            # Member Group Code
            "Communication Log",                                # Main Category
            note.action_notes or "N/A",                         # Enquiry Selection
            "N/A",                                              # Grouping
            "Completed"                                         # Status
        ])

    # 6. Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except: pass
        ws.column_dimensions[column_letter].width = max_length + 3

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"Delegation_Flow_Report_{timezone.now().strftime('%Y-%m-%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    
    return response

from datetime import datetime
from django.utils.dateparse import parse_date
from django.conf import settings

@login_required
def final_sla_report_view(request):

    start_str = request.GET.get('start_date')
    end_str = request.GET.get('end_date')
    
    # 1. Setup Date Filters with proper day boundaries (Start of day to End of day)
    delegate_q = Q()
    notes_q = Q()
    email_log_q = Q()

    if start_str and start_str != "None" and start_str != "":
        parsed_start = parse_date(start_str)
        if parsed_start:
            start_dt = datetime.combine(parsed_start, datetime.min.time())
            if settings.USE_TZ:
                start_dt = timezone.make_aware(start_dt)
            delegate_q &= Q(received_timestamp__gte=start_dt)
            notes_q &= Q(date__gte=start_dt)
            email_log_q &= Q(sent_at__gte=start_dt)

    if end_str and end_str != "None" and end_str != "":
        parsed_end = parse_date(end_str)
        if parsed_end:
            # Set to 23:59:59 so records created on the final day are fully included
            end_dt = datetime.combine(parsed_end, datetime.max.time())
            if settings.USE_TZ:
                end_dt = timezone.make_aware(end_dt)
            delegate_q &= Q(received_timestamp__lte=end_dt)
            notes_q &= Q(date__lte=end_dt)
            email_log_q &= Q(sent_at__lte=end_dt)

    # 2. Handle Excel Export Request
    if request.GET.get('export') == 'excel':
        return export_sla_excel(delegate_q, notes_q, email_log_q)

    # 3. Aggregate Grouped Totals
    calls_breakdown = ClientNotes.objects.filter(
        notes_q, 
        communication_type__in=['Incoming Call', 'Outgoing Call']
    ).values('communication_type', 'action_notes').annotate(total=Count('id')).order_by('communication_type')

    inbox_breakdown = CrmDelegateTo.objects.filter(delegate_q).values(
        'type', 'status'
    ).annotate(total=Count('email_id')).order_by('type')

    queries_breakdown = ClientNotes.objects.filter(
        notes_q, 
        communication_type='Notes Log'
    ).values('action_notes').annotate(total=Count('id')).order_by('action_notes')

    sent_emails_breakdown = DirectEmailLog.objects.filter(email_log_q).values(
        'subject' 
    ).annotate(total=Count('id'))

    teams_breakdown = ClientNotes.objects.filter(
        notes_q, 
        communication_type='Teams Meeting'
    ).values('action_notes').annotate(total=Count('id')).order_by('action_notes')

    # 4. Final Data Structure with Badge Totals
    report_data = {
        'CALLS': calls_breakdown,
        'CALLS_TOTAL': sum(item['total'] for item in calls_breakdown),
        
        'INBOX_EMAILS': inbox_breakdown,
        'INBOX_TOTAL': sum(item['total'] for item in inbox_breakdown),
        
        'QUERIES': queries_breakdown,
        'QUERIES_TOTAL': sum(item['total'] for item in queries_breakdown),
        
        'SENT_EMAILS': sent_emails_breakdown,
        'SENT_TOTAL': sum(item['total'] for item in sent_emails_breakdown),
        
        'TEAMS': teams_breakdown,
        'TEAMS_TOTAL': sum(item['total'] for item in teams_breakdown),
    }

    grand_total = (
        report_data['CALLS_TOTAL'] + 
        report_data['INBOX_TOTAL'] + 
        report_data['QUERIES_TOTAL'] + 
        report_data['SENT_TOTAL'] + 
        report_data['TEAMS_TOTAL']
    )

    details = ClientNotes.objects.filter(notes_q).order_by('-date')[:50]

    context = {
        'report': report_data,
        'grand_total': grand_total,
        'start_date': start_str,
        'end_date': end_str,
        'details': details,
    }
    return render(request, 'final_sla_report.html', context)

def export_sla_excel(delegate_q, notes_q, email_log_q):
    """
    MASTER SLA EXCEL EXPORT (Filtered by date range)
    """
    wb = openpyxl.Workbook()
    
    # --- STYLING ---
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1B5E20", end_color="1B5E20", fill_type="solid")
    headers = [
        'Status/Type', 'Date Received', 'Date Actioned', 'Delegator', 
        'Delegated to/Action By', 'Communication Type', 'Enquiry Category (1-14)', 
        'Action Notes', 'Reference', 'Content Preview', 'Destination'
    ]

    # ==========================================================================
    # SHEET 1: MASTER AUDIT TRAIL
    # ==========================================================================
    ws1 = wb.active
    ws1.title = "Master SLA Audit Trail"
    ws1.append(headers)
    for cell in ws1[1]:
        cell.font, cell.fill, cell.alignment = header_font, header_fill, Alignment(horizontal="center")

    # 1. DELEGATED (Respecting delegate_q)
    for task in CrmDelegateTo.objects.filter(delegate_q):
        inbox_record = CrmInbox.objects.filter(email_id=task.email_id).first()
        received_dt = inbox_record.received_timestamp.replace(tzinfo=None) if inbox_record and inbox_record.received_timestamp else task.received_timestamp.replace(tzinfo=None)
        actioned_dt = None
        if task.status == 'Completed':
            comp = CrmDelegateAction.objects.filter(task_email_id=task.email_id, action_type='complete').order_by('-action_timestamp').first()
            actioned_dt = comp.action_timestamp.replace(tzinfo=None) if comp else task.received_timestamp.replace(tzinfo=None)
        ws1.append([task.status, received_dt, actioned_dt, task.delegated_by, task.delegated_to, 'Inbox Delegation', CATEGORY_NAMES.get(str(task.category), task.category), task.type, getattr(task, 'member_group_code', '---'), task.subject, getattr(task, 'sender', '---')])

    # 2. DIRECT & DELEGATED NOTES (Respecting notes_q)
    for note in ClientNotes.objects.filter(notes_q):
        display_label = "Direct Note"
        clean_comm_type = note.communication_type or "Note"
        if note.communication_type and "Delegated:" in note.communication_type:
            display_label = "Delegated Note"
            clean_comm_type = note.communication_type.replace("Delegated: ", "")
        ws1.append([display_label, None, note.date.replace(tzinfo=None), None, note.user, clean_comm_type, None, note.action_notes, note.related_member_group_code, note.notes[:250], None])

    # 3. DIRECT EMAILS (Respecting email_log_q)
    for email in DirectEmailLog.objects.filter(email_log_q):
        ws1.append(['Direct Email', None, email.sent_at.replace(tzinfo=None), None, email.sent_by_user.username, 'Direct Email', '', email.action_type, getattr(email, 'member_group_code', '---'), email.subject, email.recipient_email])

    # 4. THREAD REPLIES (Respecting date range of tasks)
    # We only show replies for tasks that passed the delegate_q filter
    filtered_email_ids = CrmDelegateTo.objects.filter(delegate_q).values_list('email_id', flat=True)
    for action in CrmDelegateAction.objects.filter(action_type='REPLY_SENT', task_email_id__in=filtered_email_ids):
        parent = CrmDelegateTo.objects.filter(email_id=action.task_email_id).first()
        ws1.append([
            'Reply Sent (Thread)', None, action.action_timestamp.replace(tzinfo=None), None, action.action_user, 
            'Sent Email (Reply)', None, action.note_content, 
            getattr(parent, 'member_group_code', '---') if parent else '---', action.related_subject, 
            getattr(parent, 'sender', '---') if parent else '---'
        ])

    # ==========================================================================
    # SHEET 2: AGENT SUMMARY (Respecting date range for each agent's actions)
    # ==========================================================================
    ws2 = wb.create_sheet(title="Agent Summary")
    ws2.append(headers)
    for cell in ws2[1]:
        cell.font, cell.fill, cell.alignment = header_font, header_fill, Alignment(horizontal="center")

    # Get unique agents across all filtered query sets
    agents = set(CrmDelegateTo.objects.filter(delegate_q).values_list('delegated_to', flat=True)) | \
             set(ClientNotes.objects.filter(notes_q).values_list('user', flat=True)) | \
             set(DirectEmailLog.objects.filter(email_log_q).values_list('sent_by_user__username', flat=True))

    for agent in sorted(filter(None, agents)):
        agent_fill = PatternFill(start_color="D1D5DB", end_color="D1D5DB", fill_type="solid")
        row_num = ws2.max_row + 1
        ws2.append([f"AGENT: {agent.upper()}"])
        ws2.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=11)
        ws2.cell(row=row_num, column=1).font = Font(bold=True)
        ws2.cell(row=row_num, column=1).fill = agent_fill

        # Filtered Agent Data
        for t in CrmDelegateTo.objects.filter(delegate_q, delegated_to=agent):
            ws2.append([t.status, None, None, t.delegated_by, t.delegated_to, 'Inbox Delegation', t.category, t.type, t.member_group_code, t.subject, '---'])
        
        for n in ClientNotes.objects.filter(notes_q, user=agent):
            display_label = "Delegated Note" if "Delegated:" in (n.communication_type or "") else "Direct Note"
            ws2.append([display_label, None, n.date.replace(tzinfo=None), None, n.user, (n.communication_type or "Note"), None, n.action_notes, n.related_member_group_code, n.notes[:100], None])
        
        for e in DirectEmailLog.objects.filter(email_log_q, sent_by_user__username=agent):
            ws2.append(['Direct Email', None, e.sent_at.replace(tzinfo=None), None, agent, 'Direct Email', '', e.action_type, e.member_group_code, e.subject, e.recipient_email])

        for r in CrmDelegateAction.objects.filter(action_type='REPLY_SENT', action_user=agent, task_email_id__in=filtered_email_ids):
            ws2.append(['Reply Sent (Thread)', None, r.action_timestamp.replace(tzinfo=None), None, agent, 'Sent Email (Reply)', None, r.note_content, '---', r.related_subject, '---'])

        ws2.append([]) 

    for sheet in [ws1, ws2]:
        for col in sheet.columns:
            sheet.column_dimensions[col[0].column_letter].width = 25

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="SLA_Master_Report_{date.today()}.xlsx"'
    wb.save(response)
    return response

from django.utils.dateparse import parse_date

def get_date_filters(request):
    """Helper function to extract dates safely from GET request"""
    start_str = request.GET.get('start_date')
    end_str = request.GET.get('end_date')
    
    # Check if the string is empty or literally the string "None"
    def is_valid(val):
        return val and isinstance(val, str) and val.strip() not in ["None", ""]

    filters = Q()
    
    if is_valid(start_str):
        try:
            # 🚀 FIX: Use standard datetime.strptime instead of missing parse_date import
            parsed_start = datetime.strptime(start_str.strip(), "%Y-%m-%d").date()
            filters &= Q(received_timestamp__gte=parsed_start)
        except ValueError:
            pass
            
    if is_valid(end_str):
        try:
            # 🚀 FIX: Use standard datetime.strptime instead of missing parse_date import
            parsed_end = datetime.strptime(end_str.strip(), "%Y-%m-%d").date()
            next_day = parsed_end + timedelta(days=1)
            filters &= Q(received_timestamp__lt=next_day)
        except ValueError:
            pass
            
    return filters, start_str, end_str


def get_unified_email_data(request):
    """
    Helper function to merge CrmInbox (New) and CrmDelegateTo (Delegated) 
    data into a single list for the UI and CSV Export.
    - Received Date comes strictly from CrmInbox (or synced lookup).
    - Delegated Date comes strictly from CrmDelegateTo.received_timestamp.
    """
    # 1. Action Lookup (Check for replies and user mappings)
    last_reply_map = CrmDelegateAction.objects.filter(
        action_type='REPLY_SENT'
    ).values('task_email_id').annotate(last_replied=Max('action_timestamp'))
    last_reply_dict = {item['task_email_id']: item['last_replied'] for item in last_reply_map if item.get('task_email_id')}

    delegation_user_map = CrmDelegateAction.objects.filter(
        action_type='restore_to_inbox' 
    ).values('task_email_id', 'action_user')
    user_dict = {item['task_email_id']: item['action_user'] for item in delegation_user_map if item.get('task_email_id')}

    action_notes_qs = CrmDelegateAction.objects.exclude(
        note_content__isnull=True
    ).exclude(
        note_content__exact=''
    ).values('task_email_id', 'note_content', 'action_timestamp').order_by('action_timestamp')

    action_note_map = {}
    for note in action_notes_qs:
        eid = note.get('task_email_id')
        content = str(note.get('note_content') or '').strip()
        if eid and content:
            if eid in action_note_map:
                action_note_map[eid] += f" | {content}"
            else:
                action_note_map[eid] = content

    # 2. Setup Filters 
    date_filter, _, _ = get_date_filters(request)

    # 3. Fetch Delegated Emails (CrmDelegateTo)
    delegated_qs = CrmDelegateTo.objects.filter(date_filter).order_by('-received_timestamp')
    delegated_ids = {getattr(task, 'email_id') for task in delegated_qs if getattr(task, 'email_id', None)}

    # Map CrmInbox received_timestamps by email_id so we can look them up instantly
    inbox_received_map = {
        item.email_id: item.received_timestamp 
        for item in CrmInbox.objects.filter(email_id__in=delegated_ids)
    }

    # 4. Fetch New/Pending Emails (CrmInbox)
    new_emails_qs = CrmInbox.objects.filter(date_filter).exclude(
        email_id__in=delegated_ids
    ).order_by('-received_timestamp')

    unified_list = []
    
    try:
        cat_dict = CATEGORY_NAMES
    except NameError:
        cat_dict = {}

    # Process Delegated Items (CrmDelegateTo)
    for task in delegated_qs:
        eid = getattr(task, 'email_id', '')
        
        # 🟢 Received Date comes from CrmInbox lookup, fallback to CrmDelegateTo if needed
        received_time = inbox_received_map.get(eid) or getattr(task, 'arrival_timestamp', None)
        
        # 🟢 Delegated Date pulls strictly from CrmDelegateTo.received_timestamp
        delegated_time = getattr(task, 'received_timestamp', None)

        unified_list.append({
            'email_id': eid,
            'subject': getattr(task, 'subject', 'No Subject') or "No Subject",
            'sender': getattr(task, 'sender', 'Unknown') or "Unknown",
            'status': getattr(task, 'status', 'Delegated'),
            'delegated_to': getattr(task, 'delegated_to', None) or user_dict.get(eid, "System"),
            'member_group_code': getattr(task, 'member_group_code', getattr(task, 'Member_Group_Code', 'N/A')),
            
            'membership_number': getattr(task, 'mip_number', getattr(task, 'membership_number', 'N/A')), 
            'id_passport': getattr(task, 'id_passport', 'N/A'),
            
            'category': cat_dict.get(str(getattr(task, 'category', '')), getattr(task, 'category', 'Unclassified')),
            'type': getattr(task, 'type', 'None'), 
            
            'received_timestamp': received_time,      # From CrmInbox via mapping
            'delegated_timestamp': delegated_time,    # Strictly from CrmDelegateTo.received_timestamp
            'last_replied_timestamp': last_reply_dict.get(eid),
            
            'action_note': action_note_map.get(eid, ''),
            'is_delegated': True
        })

    # Process New Items (CrmInbox)
    for email in new_emails_qs:
        eid = getattr(email, 'email_id', '')
        unified_list.append({
            'email_id': eid,
            'subject': getattr(email, 'subject', 'No Subject') or "No Subject",
            'sender': getattr(email, 'sender', 'Unknown') or "Unknown",
            'status': 'New',
            'delegated_to': 'Inbox (Unassigned)',
            'member_group_code': getattr(email, 'Member_Group_Code', getattr(email, 'member_group_code', 'N/A')),
            
            'membership_number': 'N/A',
            'id_passport': getattr(email, 'id_passport', 'N/A'),
            
            'category': getattr(email, 'category', 'Unclassified'),
            'type': getattr(email, 'type', 'Incoming Email'), 
            
            'received_timestamp': getattr(email, 'received_timestamp', None), # From CrmInbox
            'delegated_timestamp': None,                                       # None because it's not delegated yet
            'last_replied_timestamp': None,
            
            'action_note': action_note_map.get(eid, ''),
            'is_delegated': False
        })

    # 5. Search Filter
    search_text = request.GET.get('search', '').lower()
    if search_text:
        unified_list = [
            row for row in unified_list 
            if search_text in str(row.get('subject', '')).lower() or 
               search_text in str(row.get('sender', '')).lower() or 
               search_text in str(row.get('member_group_code', '')).lower()
        ]

    # Final Sort
    fallback_date = timezone.now().replace(year=1900)
    unified_list.sort(key=lambda x: x['received_timestamp'] or fallback_date, reverse=True)
    return unified_list

@login_required
def email_workflow_log_view(request):
    data = get_unified_email_data(request)
    
    paginator = Paginator(data, 25) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'email_workflow_log.html', {'page_obj': page_obj})

@login_required
def export_email_workflow_csv(request):
    data = get_unified_email_data(request)
    
    # --- 🚀 BULK FETCH NOTES FROM crm_delegate_actions ---
    email_ids = [row['email_id'] for row in data if row.get('email_id')]
    notes_dict = {}
    
    if email_ids:
        # Fetch actions with non-empty note_content for the current emails, ordered by timestamp
        notes_qs = CrmDelegateAction.objects.filter(
            task_email_id__in=email_ids
        ).exclude(
            note_content__isnull=True
        ).exclude(
            note_content__exact=''
        ).values('task_email_id', 'note_content', 'action_user', 'action_timestamp').order_by('action_timestamp')
        
        for note in notes_qs:
            eid = note.get('task_email_id')
            # Safe string cast
            content = str(note.get('note_content') or '').strip()
            
            if not content or not eid:
                continue
                
            formatted_note = content
            
            if eid in notes_dict:
                notes_dict[eid] += f" | {formatted_note}"
            else:
                notes_dict[eid] = formatted_note
    # ---------------------------------------------------
    
    response = HttpResponse(content_type='text/csv')
    filename = f"Email_Workflow_{timezone.now().strftime('%Y-%m-%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    
    # 🚀 ADDED 'Delegated Date' AND KEPT ALL EXISTING HEADERS
    writer.writerow([
        'Received Date', 
        'Delegated Date',
        'Sender', 
        'Subject', 
        'Status', 
        'Agent (Assigned)', 
        'Member Group Code',    
        'Membership Number',    
        'ID/Passport Number',   
        'Category',
        'Enquiry Selection', 
        'Date Replied',
        'Notes'
    ])

    for row in data:
        # Safely check if received_timestamp exists before calling strftime
        received_dt = row['received_timestamp'].strftime('%Y-%m-%d %H:%M') if row.get('received_timestamp') else 'N/A'
        delegated_dt = row['delegated_timestamp'].strftime('%Y-%m-%d %H:%M') if row.get('delegated_timestamp') else 'N/A'
        
        reply_dt = 'No Reply'
        if row.get('last_replied_timestamp'):
            reply_dt = row['last_replied_timestamp'].strftime('%Y-%m-%d %H:%M')

        agent_name = row.get('delegated_to') or 'Inbox (Unassigned)'
        
        # Pull note matching task_email_id (or fallback to row['action_note'])
        email_note = notes_dict.get(row['email_id'], row.get('action_note', ''))

        writer.writerow([
            received_dt,
            delegated_dt,
            row.get('sender', 'Unknown'),
            row.get('subject', 'No Subject'),
            row.get('status', 'New'),
            agent_name,
            row.get('member_group_code', 'N/A'),
            row.get('membership_number', 'N/A'),
            row.get('id_passport', 'N/A'),       
            row.get('category', 'Unclassified'),
            row.get('type', 'None'),
            reply_dt,
            email_note
        ])

    return response

@login_required
def download_actual_email(request, email_id):
    """
    Downloads either:
    - The specific Reply (.eml) when ?action_id=<id> is provided.
    - The Original Incoming or Direct Sent Email (.eml) from local disk (or synthesized with exact Outlook-compatible MIME headers).
    """
    import re
    from email.message import EmailMessage as PyEmailMessage
    from email.policy import SMTP as SMTP_POLICY
    from email.utils import format_datetime, make_msgid

    action_id = request.GET.get('action_id')
    inbox_item, delegate_item, direct_item, body_html, _ = _ensure_local_email_data(email_id)
    source_obj = delegate_item or inbox_item or direct_item

    # Use a policy with unlimited line length on headers so long MIME types (.xlsx/.docx) are NEVER RFC2047-encoded
    clean_mime_policy = SMTP_POLICY.clone(max_line_length=0)

    def _set_outlook_html_body(msg_obj, raw_html):
        """
        Sets a direct text/html body (matching the working Reply .eml format)
        and strips HTML comments so Outlook never renders raw tags.
        """
        cleaned_html = re.sub(r'<!--.*?-->', '', raw_html or '', flags=re.DOTALL).strip()
        msg_obj.set_content(cleaned_html, subtype='html', charset='utf-8', cte='quoted-printable')

    def _safe_mime_type(filename_str, fallback_ctype=None):
        """
        Returns a clean (maintype, subtype) tuple that never triggers header folding in Outlook.
        """
        ctype = fallback_ctype or mimetypes.guess_type(filename_str)[0] or 'application/octet-stream'
        if '/' not in ctype:
            return 'application', 'octet-stream'
        maintype, subtype = ctype.split('/', 1)
        return maintype.strip(), subtype.strip()

    # CASE 1: Downloading a specific REPLY (.eml)
    if action_id and str(action_id).isdigit():
        reply_action = get_object_or_404(CrmDelegateAction, pk=int(action_id), task_email_id=email_id)
        reply_subject = reply_action.related_subject or getattr(source_obj, 'subject', 'Reply') or 'Reply'
        clean_subject = "".join([c for c in reply_subject if c.isalnum() or c in (' ', '-', '_', ':')]).replace(':', '_').strip()
        filename = f"{clean_subject[:60] or 'reply_record'}.eml"

        actual_to, clean_log_note = _resolve_reply_recipient(reply_action, source_obj)

        msg = PyEmailMessage(policy=clean_mime_policy)
        msg['Subject'] = reply_subject
        msg['From'] = getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'Unity@futurasa.co.za')
        msg['To'] = actual_to
        if reply_action.cc_recipients:
            msg['Cc'] = reply_action.cc_recipients
        if reply_action.bcc_recipients:
            msg['Bcc'] = reply_action.bcc_recipients

        dt = reply_action.action_timestamp or timezone.now()
        msg['Date'] = format_datetime(timezone.localtime(dt) if timezone.is_aware(dt) else dt)
        msg['Message-ID'] = make_msgid(domain='futurasa.co.za')

        reply_html = reply_action.body or clean_log_note or ""
        _set_outlook_html_body(msg, reply_html)

        # Attach any files that were sent with this reply
        if reply_action.attachment_path:
            paths = [p.strip() for p in reply_action.attachment_path.split(',') if p.strip()]
            for rel_p in paths:
                abs_p = os.path.join(settings.MEDIA_ROOT, rel_p)
                if os.path.exists(abs_p):
                    orig_name = os.path.basename(abs_p)
                    if orig_name.startswith('reply_'):
                        parts = orig_name.split('_', 2)
                        orig_name = parts[2] if len(parts) == 3 and parts[1].isdigit() else orig_name[len('reply_'):]
                    maintype, subtype = _safe_mime_type(orig_name)
                    with open(abs_p, 'rb') as f:
                        msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=orig_name)
        elif reply_action.attachment_name:
            names = [n.strip() for n in reply_action.attachment_name.split(',') if n.strip()]
            reply_atts = CrmEmailAttachment.objects.filter(email_id=email_id, attachment_id__startswith='local_reply_')
            for name in names:
                matched = reply_atts.filter(name=name).first()
                if matched:
                    abs_p = os.path.join(settings.MEDIA_ROOT, matched.file_path)
                    if os.path.exists(abs_p):
                        maintype, subtype = _safe_mime_type(matched.name, matched.content_type)
                        with open(abs_p, 'rb') as f:
                            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=matched.name)

        response = HttpResponse(msg.as_bytes(policy=clean_mime_policy), content_type='message/rfc822')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    # CASE 2: Downloading the ORIGINAL INCOMING or DIRECT SENT Email (.eml)
    filename = "email_record.eml"
    if source_obj and getattr(source_obj, 'subject', None):
        clean_subject = "".join([c for c in source_obj.subject if c.isalnum() or c in (' ', '-', '_')]).strip()
        if clean_subject:
            filename = f"{clean_subject[:50]}.eml"

    # 1. Check if the raw .eml file is already saved on local disk
    eml_rel_path = getattr(delegate_item, 'eml_file_path', None) or getattr(inbox_item, 'eml_file_path', None)
    if eml_rel_path:
        abs_eml_path = os.path.join(settings.MEDIA_ROOT, eml_rel_path)
        if os.path.exists(abs_eml_path):
            return FileResponse(open(abs_eml_path, 'rb'), as_attachment=True, filename=filename, content_type='message/rfc822')

    # 2. Synthesize a clean Outlook-compatible .eml file from local database + local CrmEmailAttachment files
    if source_obj:
        msg = PyEmailMessage(policy=clean_mime_policy)
        msg['Subject'] = getattr(source_obj, 'subject', 'No Subject') or 'No Subject'
        if direct_item and not (inbox_item or delegate_item):
            msg['From'] = getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'Unity@futurasa.co.za')
            msg['To'] = getattr(direct_item, 'recipient_email', '') or ''
        else:
            msg['From'] = getattr(source_obj, 'sender', '') or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'Unity@futurasa.co.za')
            msg['To'] = getattr(source_obj, 'to_recipients', '') or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'Unity@futurasa.co.za')

        if getattr(source_obj, 'cc_recipients', None):
            msg['Cc'] = source_obj.cc_recipients
        if getattr(source_obj, 'bcc_recipients', None):
            msg['Bcc'] = source_obj.bcc_recipients

        dt = getattr(source_obj, 'received_timestamp', None) or getattr(source_obj, 'sent_at', None) or timezone.now()
        msg['Date'] = format_datetime(timezone.localtime(dt) if timezone.is_aware(dt) else dt)
        msg['Message-ID'] = make_msgid(domain='futurasa.co.za')

        _set_outlook_html_body(msg, body_html or "")

        # Attach all local non-inline attachments belonging to this email (including local_direct_ attachments)
        local_atts = (
            CrmEmailAttachment.objects
            .filter(email_id=email_id, is_inline=False)
            .exclude(attachment_id__startswith='local_reply_')
            .order_by('id')
        )
        for att in local_atts:
            abs_p = os.path.join(settings.MEDIA_ROOT, att.file_path)
            if os.path.exists(abs_p):
                maintype, subtype = _safe_mime_type(att.name, att.content_type)
                with open(abs_p, 'rb') as f:
                    msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=att.name)

        response = HttpResponse(msg.as_bytes(policy=clean_mime_policy), content_type='message/rfc822')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    messages.error(request, "Email record not found.")
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


def download_member_note_file(request, member_group_code):
    raw_filename = request.GET.get('file')
    if not raw_filename:
        raise Http404("No file specified")

    target_filename = urllib.parse.unquote(raw_filename)

    # Precise lookup
    document = MemberDocument.objects.filter(
        related_member_group_code=member_group_code,
        document_file__icontains=target_filename
    ).first()

    if document and document.document_file:
        file_path = document.document_file.path
        if os.path.exists(file_path):
            # Stream the file
            return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=target_filename)

    # If we get here, the file doesn't exist.
    # Instead of a silent 302, we show an error.
    messages.error(request, f"Attachment '{target_filename}' could not be found.")
    return redirect('member_information', member_group_code=member_group_code)


def far_inbox_view(request):
    """
    Placeholder view for FAR Delegations.
    Currently, this is a stub and should be implemented with actual logic.
    """
    messages.info(request, "FAR Delegations feature is under development.")
    return render(request, 'far_inbox.html', {})


@login_required
def view_email_thread(request, email_id):
    """
    Renders either:
    - 'incoming' mode (when clicking View on an ORIGINAL/Incoming email): shows ONLY the incoming email & its attachments.
    - 'reply' mode (when clicking View on a REPLY row with ?action_id=<id>): shows ONLY that specific Reply Sent section.
    """
    action_id = request.GET.get('action_id')
    inbox_item, delegate_item, direct_item, email_body, attachments_list = _ensure_local_email_data(email_id)

    is_direct = bool(direct_item and not delegate_item)
    task = delegate_item or direct_item or inbox_item
    if not task:
        raise Http404("No email record found for this ID.")

    # Resolve sender, To, CC, BCC, and Received Date for the incoming email header
    sender_email = (
        getattr(inbox_item, 'sender', None)
        or getattr(delegate_item, 'sender', None)
        or getattr(direct_item, 'sender_email', None)
        or 'Unknown'
    )
    sender_name = (
        getattr(inbox_item, 'sender_name', None)
        or getattr(delegate_item, 'sender_name', None)
        or sender_email
    )
    cc_recipients = (
        getattr(inbox_item, 'cc_recipients', None)
        or getattr(delegate_item, 'cc_recipients', None)
        or getattr(direct_item, 'cc_recipients', None)
        or ''
    )
    bcc_recipients = (
        getattr(inbox_item, 'bcc_recipients', None)
        or getattr(delegate_item, 'bcc_recipients', None)
        or getattr(direct_item, 'bcc_recipients', None)
        or ''
    )

    # Map reply attachments stored locally so they can be downloaded from the Reply card
    reply_atts_qs = CrmEmailAttachment.objects.filter(
        email_id=email_id,
        attachment_id__startswith='local_reply_'
    ).order_by('id')

    if action_id and str(action_id).isdigit():
        view_mode = 'reply'
        actions = list(CrmDelegateAction.objects.filter(pk=int(action_id), task_email_id=email_id))
    else:
        view_mode = 'incoming'
        actions = list(
            CrmDelegateAction.objects
            .filter(task_email_id=email_id)
            .exclude(action_type='REPLY_SENT')
            .order_by('action_timestamp')
        )

    # Attach downloadable file objects and resolved To/Log Type to each REPLY_SENT action
    for act in actions:
        act.downloadable_files = []
        if act.action_type == 'REPLY_SENT':
            act.to_recipients, act.clean_log_type = _resolve_reply_recipient(act, task)

            if act.attachment_name:
                names = [n.strip() for n in act.attachment_name.split(',') if n.strip()]
                for name in names:
                    matched_att = next((a for a in reply_atts_qs if a.name == name), None)
                    if matched_att:
                        act.downloadable_files.append({
                            'name': matched_att.name,
                            'url': reverse('serve_local_attachment', kwargs={'att_pk': matched_att.id})
                        })
                    else:
                        act.downloadable_files.append({
                            'name': name,
                            'url': None
                        })

    context = {
        'task': task,
        'is_direct': is_direct,
        'inbox_item': inbox_item,
        'actions': actions,
        'email_body': email_body,
        'attachments': attachments_list,
        'email_id': email_id,
        'view_mode': view_mode,
        'action_id': action_id,
        'sender_name': sender_name,
        'sender_email': sender_email,
        'cc_recipients': cc_recipients,
        'bcc_recipients': bcc_recipients,
    }
    return render(request, 'email_thread.html', context)