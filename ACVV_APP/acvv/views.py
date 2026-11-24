import base64
import csv
import mimetypes
import os
import re
import logging
from itertools import count
from datetime import datetime, timedelta
import traceback
import urllib.parse

# Django Imports
from django.http import HttpResponse, StreamingHttpResponse, FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, OuterRef, Subquery, Sum, Count, Avg
from django.db.models.functions import TruncMonth
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.safestring import mark_safe
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string

# Third-Party Imports
import pandas as pd
import requests
import openpyxl
from openpyxl.styles import PatternFill, Border, Side, Alignment, Font
from openpyxl.utils import get_column_letter
from dateutil import parser
from dateutil.relativedelta import relativedelta

# Local Project Imports
from .models import (
    AcvvClaim, AcvvEmailAttachment, BranchDocument, ClaimNote, Globalacvv, ClientNotes, 
    EmailDelegation, DelegationNote, DelegationTransactionLog, 
    ReconciliationRecord, ReconciliationWorksheet, TempExit
)
from .services.outlook_graph_service import OutlookGraphService
from .services.delegation_service import (
    get_or_create_delegation_status, 
    delegate_email_task, 
    add_delegation_note, 
    get_delegated_emails_for_user,
    log_delegation_transaction,
    ingest_single_email_from_graph,
    sync_new_inbox_emails,
    save_outgoing_email_locally,
    download_raw_eml_to_disk,
    download_and_link_attachments,
    build_clean_eml_bytes,
    _is_duplicate_worked_email
)

# Initialize logger
logger = logging.getLogger(__name__)

def _ensure_local_email_data(delegation, target_email=None):
    """
    Ensures an incoming EmailDelegation row has its HTML body, metadata, attachments,
    inline cid: images, and .eml file saved locally. Never deletes the task on 404.
    """
    if not delegation or not delegation.email_id:
        return delegation

    eid = str(delegation.email_id)
    if eid.startswith(('SENT-', 'REPLY-', 'LOCAL-', 'CLAIM-', 'DIRECT_')) or delegation.status == 'SENT':
        return delegation

    target_email = target_email or getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'lorraine@futurasa.co.za')

    needs_full_sync = (not delegation.is_fully_synced) or (not delegation.body)
    needs_att_heal = (
        (delegation.has_attachments or (delegation.body and 'cid:' in delegation.body.lower()))
        and not AcvvEmailAttachment.objects.filter(email_id=eid).exists()
    )

    if needs_full_sync:
        refreshed = ingest_single_email_from_graph(eid, target_email=target_email, force_refresh=True)
        if refreshed:
            return refreshed
    elif needs_att_heal:
        rewritten_body, has_non_inline = download_and_link_attachments(
            email_id=eid,
            body_html=delegation.body or '',
            target_email=target_email,
            has_attachments=True,
        )
        delegation.body = rewritten_body
        delegation.has_attachments = bool(has_non_inline)
        delegation.save(update_fields=['body', 'has_attachments'])

    return delegation


def _get_local_attachments_for_email(email_id, legacy_attachment=None):
    """
    Returns a standardized list of downloadable non-inline attachment dicts
    from AcvvEmailAttachment (plus any legacy FileField attachment fallback).
    """
    built = []
    seen_names = set()

    if email_id:
        local_atts = AcvvEmailAttachment.objects.filter(
            email_id=str(email_id),
            is_inline=False
        ).order_by('id')
        for att in local_atts:
            url = reverse('serve_local_attachment', args=[att.id])
            built.append({
                'id': att.id,
                'name': att.name,
                'size': att.size,
                'contentType': att.content_type or 'application/octet-stream',
                'url': url,
                'local_url': url,
                'is_local': True,
            })
            seen_names.add(att.name.lower())

    if legacy_attachment:
        try:
            legacy_name = os.path.basename(legacy_attachment.name)
            if legacy_name and legacy_name.lower() not in seen_names:
                built.append({
                    'id': None,
                    'name': legacy_name,
                    'size': None,
                    'contentType': mimetypes.guess_type(legacy_name)[0] or 'application/octet-stream',
                    'url': legacy_attachment.url,
                    'local_url': legacy_attachment.url,
                    'is_local': True,
                })
        except Exception:
            pass

    return built

def login_view(request):
    """
    Handles user login.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
    
    form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

from acvv.services.outlook_graph_service import OutlookGraphService

@login_required
def delete_global_claim(request, claim_id):
    """Securely delete an ACVV claim (supports both Two-Pot and standard global claims)."""
    if request.method == 'POST':
        claim = get_object_or_404(AcvvClaim, id=claim_id)
        claim_type = claim.claim_type
        member_name = f"{claim.member_surname}, {claim.member_name}"
        
        try:
            claim.delete()
            messages.success(request, f"Claim for {member_name} has been successfully deleted.")
        except Exception as e:
            print(f"\n❌ [CRITICAL DATABASE DELETE ERROR]: {str(e)}\n")
            messages.error(request, f"Failed to delete claim: {str(e)}")
            
        # Redirect back to the correct dashboard depending on claim type
        if claim_type == 'Two Pot':
            return redirect('global_two_pot')
        return redirect('global_claims')
        
    return redirect('global_claims')

@login_required
def test_graph_access(request):
    # This calls the root level without looking into a specific email item
    # It checks if the app can even "talk" to the mailbox at all
    response = OutlookGraphService.fetch_outlook_data("mailFolders", settings.OUTLOOK_EMAIL_ADDRESS)
    return HttpResponse(str(response))

@login_required
def dashboard(request):
    username = request.user.username
    is_outlook_admin = request.user.username.lower() == 'omega' or request.user.is_superuser

    # Build normalized index of all worked emails to exclude old-ID vs. ImmutableId duplicates from count
    worked_index = {}
    for subj, sender, recv in EmailDelegation.objects.exclude(status='NEW').values_list('subject', 'sender_address', 'received_at'):
        key = ((subj or '').strip().lower(), (sender or '').strip().lower())
        worked_index.setdefault(key, []).append(recv)

    new_rows = EmailDelegation.objects.filter(status='NEW', work_related=True).values_list('id', 'subject', 'sender_address', 'received_at')
    undelegated_count = 0
    for _, subj, sender, recv in new_rows:
        if not _is_duplicate_worked_email(subj, sender, recv, worked_index):
            undelegated_count += 1

    recycled_count = EmailDelegation.objects.filter(status='DLT').count()
    my_tasks_count = EmailDelegation.objects.filter(assigned_user=request.user, status='DEL').count()

    context = {
        'username': username,
        'undelegated_count': undelegated_count,
        'recycled_count': recycled_count,
        'my_tasks_count': my_tasks_count,
        'is_outlook_admin': is_outlook_admin,
    }
    return render(request, 'dashboard.html', context)


def logout_view(request):
    """Logs the user out."""
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')


def index(request):
    """Handles the root URL, redirecting to the login page."""
    return redirect('login')


@login_required
def outlook_dashboard_view(request):
    if request.user.username.lower() != 'omega' and not request.user.is_superuser:
        messages.error(request, "Access restricted.")
        return redirect('outlook_delegated_box')

    target_email = request.GET.get('email', settings.OUTLOOK_EMAIL_ADDRESS)
    context = {'target_email': target_email, 'messages': []}

    # Manual Sync with Outlook (?sync=true) — polls Graph ONLY when requested
    if request.GET.get('sync') == 'true':
        synced_count, sync_error = sync_new_inbox_emails(target_email=target_email, top_count=200)
        if sync_error:
            messages.error(request, f"Outlook Sync Error: {sync_error}")
        elif synced_count > 0:
            messages.success(request, f"Synced {synced_count} new email(s) from Outlook to local storage.")
        else:
            messages.info(request, "Inbox is already up to date with Outlook.")
        return redirect(f"{reverse('outlook_dashboard')}?email={target_email}")

    # Build normalized index of all worked emails (DEL, COM, CLO, DLT, SENT)
    worked_index = {}
    for subj, sender, recv in EmailDelegation.objects.exclude(status='NEW').values_list('subject', 'sender_address', 'received_at'):
        key = ((subj or '').strip().lower(), (sender or '').strip().lower())
        worked_index.setdefault(key, []).append(recv)

    new_rows = EmailDelegation.objects.filter(
        status='NEW',
        work_related=True
    ).select_related('assigned_user').order_by('-received_at', '-id')

    display_emails = []
    duplicate_new_pks = []
    seen_new_index = {}

    for row in new_rows:
        # 1. Catch & clean up any NEW duplicate of an already-worked email (old ID vs. ImmutableId)
        if _is_duplicate_worked_email(row.subject, row.sender_address, row.received_at, worked_index):
            duplicate_new_pks.append(row.pk)
            continue

        # 2. Catch & clean up duplicate NEW rows of the same email
        if _is_duplicate_worked_email(row.subject, row.sender_address, row.received_at, seen_new_index):
            duplicate_new_pks.append(row.pk)
            continue

        key = ((row.subject or '').strip().lower(), (row.sender_address or '').strip().lower())
        seen_new_index.setdefault(key, []).append(row.received_at)

        display_emails.append({
            'id': row.email_id,
            'subject': row.subject or '(No Subject)',
            'from': {
                'emailAddress': {
                    'name': row.sender_name or row.sender_address or 'Unknown',
                    'address': row.sender_address or '',
                }
            },
            'receivedDateTime': row.received_at,
            'hasAttachments': row.has_attachments,
            'snippet': row.snippet or '',
            'delegation_status': row.get_status_display(),
            'assigned_user': row.assigned_user.username if row.assigned_user else None,
            'delegation_id': row.pk,
        })

    # Permanently clear the duplicate NEW rows so they don't linger in MySQL
    if duplicate_new_pks:
        EmailDelegation.objects.filter(pk__in=duplicate_new_pks, status='NEW').delete()

    context['messages'] = display_emails
    return render(request, 'acvv_app/outlook_dashboard.html', context)


from django.template.loader import render_to_string

@login_required
def send_email_view(request):
    """
    Handles displaying the email form and processing the email submission 
    to the Microsoft Graph API. The email is sent FROM the mailbox specified by target_email.
    """
    # DELEGATION AWARENESS: Get target email from URL or settings default 
    target_email = request.GET.get('email', settings.OUTLOOK_EMAIL_ADDRESS)
    
    if request.method == 'POST':
        recipient = request.POST.get('recipient')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        
        # Simple validation
        if not all([recipient, subject, body]):
            messages.error(request, "All fields are required.")
            return render(request, 'acvv_app/send_email_form.html', {'target_email': target_email})
        
        # --- NEW: GENERATE AND APPEND SIGNATURE ---
        current_username = request.user.username.lower()
        current_firstname = request.user.first_name.lower() if request.user.first_name else ""
        
        # Default fallback
        agent_name = request.user.get_full_name() or request.user.username.replace('_', ' ').title()
        agent_title = "Administrator"

        # Match Specific Agents
        if 'timothy' in current_username or 'timothy' in current_firstname:
            agent_name = "Timothy Davids"
            agent_title = "Indexing Specialist"
        elif 'jesica' in current_username or 'jessica' in current_username or 'jesica' in current_firstname:
            agent_name = "Jesica Haynes"
            agent_title = "Reconciliations Specialist"
        elif 'luanovaneck' in current_username or 'luano' in current_firstname:
            agent_name = "Luano van Eck"
            agent_title = "Developer"
        elif 'omega' in current_username:
            agent_name = "Omega System Assistant"
            agent_title = "Automated System"

        signature_context = {
            'request': request,
            'agent_name': agent_name,
            'agent_title': agent_title,
            'logo_url': 'https://acvv.futurasa.co.za/static/images/futura_logo.png'
        }
        
        from django.template.loader import render_to_string
        signature_html = render_to_string('acvv_app/acvv_email_signature.html', signature_context)
        
        # 3. Combine the typed body with the rendered signature
        full_html_body = f"<div>{body}</div><br><br>{signature_html}"
        # ------------------------------------------

        # Call the service function, passing the target_email as the sender mailbox
        # Ensure we pass 'full_html_body' instead of the raw 'body'
        result = OutlookGraphService.send_outlook_email(target_email, recipient, subject, full_html_body, 'HTML')
        
        if result.get('success'):
            messages.success(request, f"Email sent successfully from {target_email} to {recipient}.")
            # Redirect back to the dashboard, preserving the target email
            return redirect(f"{reverse('outlook_dashboard')}?email={target_email}")
        else:
            error_message = f"Email failed to send from {target_email}. {result.get('error', 'Unknown API Error')}"
            
            # Extract details if they exist in the nested error structure
            details = result.get('details', {})
            if isinstance(details, dict) and 'error' in details and 'message' in details['error']:
                 error_message += f" Details: {details['error']['message']}"
            
            messages.error(request, error_message)
            # Render the form again with the failure message
            return render(request, 'acvv_app/send_email_form.html', {
                'recipient': recipient,
                'subject': subject,
                'body': body,
                'target_email': target_email
            })

    # Render the empty form on GET request
    return render(request, 'acvv_app/send_email_form.html', {'target_email': target_email})

@login_required
def outlook_delegated_box(request):
    delegations = EmailDelegation.objects.filter(
        assigned_user=request.user, 
        status='DEL'
    ).order_by('-delegated_at')
    
    tasks = []
    for delegation in delegations:
        tasks.append({
            'delegation_id': delegation.pk,
            'status': delegation.get_status_display(),
            'subject': delegation.subject,
            'from': delegation.sender_address,
            'mg_code': delegation.mip_names,
            'received': delegation.received_at,
            'delegated_at': delegation.delegated_at,
            'email_type': delegation.email_category,
        })
    return render(request, 'acvv_app/outlook_delegated_box.html', {'tasks': tasks})

@login_required
def outlook_delegated_action(request, delegation_id):
    """
    Allows the assigned user to view the full email (100% locally), add notes,
    update metadata, reply (with editable quoted thread, multi-attachments, CC, BCC,
    and local .eml archival), and mark as completed.
    """
    delegation = get_object_or_404(EmailDelegation, pk=delegation_id)

    if delegation.assigned_user != request.user and not request.user.is_superuser:
        messages.error(request, "You are not assigned to this task.")
        return redirect('outlook_delegated_box')

    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    delegation = _ensure_local_email_data(delegation, target_email=target_email)

    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        # 1. Handle Task Completion
        if action_type == 'complete_task':
            delegation.status = 'COM'
            delegation.save(update_fields=['status'])
            log_delegation_transaction(delegation_id, request.user, "TASK COMPLETED", "Email marked as completed.", action_type='TASK_COMPLETE')
            messages.success(request, f"Task #{delegation_id} archived.")
            return redirect('outlook_delegated_box')

        # 2. Handle Metadata Update
        elif action_type == 'update_metadata':
            delegation.mip_names = request.POST.get('mip_names')
            delegation.email_category = request.POST.get('email_category')
            delegation.communication_type = request.POST.get('communication_type')
            delegation.save(update_fields=['mip_names', 'email_category', 'communication_type'])
            log_delegation_transaction(delegation_id, request.user, "Metadata Updated", "System", action_type='METADATA_UPDATE')
            messages.success(request, "Task metadata updated.")
            return redirect('outlook_delegated_action', delegation_id=delegation_id)

        # 3. Handle Note Submission
        elif action_type == 'add_note':
            note_content = request.POST.get('note_content')
            success, message = add_delegation_note(delegation_id, request.user, note_content)

            if success:
                ClientNotes.objects.create(
                    acvv_record=Globalacvv.objects.filter(Q(mip_names=delegation.mip_names) | Q(branch_code=delegation.mip_names)).first(),
                    notes=note_content,
                    user=request.user.username,
                    date=timezone.now(),
                    communication_type="Internal Note",
                    action_note_type=delegation.email_category or "Task Note"
                )
                messages.success(request, message)
            return redirect('outlook_delegated_action', delegation_id=delegation_id)

        # 4. Handle Reply (editable local thread + local .eml & multi-attachment archive)
        elif action_type == 'send_reply':
            recipient = (request.POST.get('reply_recipient') or '').strip()
            reply_cc = (request.POST.get('reply_cc') or '').strip()
            reply_bcc = (request.POST.get('reply_bcc') or '').strip()
            subject = (request.POST.get('reply_subject') or '').strip()

            raw_body = (request.POST.get('reply_body') or '').strip()
            if '<p' in raw_body or '<br' in raw_body or '<div' in raw_body:
                formatted_body = raw_body
            else:
                formatted_body = raw_body.replace('\r\n', '<br>').replace('\n', '<br>')

            # Generate and append user signature
            current_username = request.user.username.lower()
            current_firstname = request.user.first_name.lower() if request.user.first_name else ""

            agent_name = request.user.get_full_name() or request.user.username.replace('_', ' ').title()
            agent_title = "Administrator"

            if 'timothy' in current_username or 'timothy' in current_firstname:
                agent_name = "Timothy Davids"
                agent_title = "Indexing Specialist"
            elif 'jesica' in current_username or 'jessica' in current_username or 'jesica' in current_firstname:
                agent_name = "Jesica Haynes"
                agent_title = "Reconciliations Specialist"
            elif 'luanovaneck' in current_username or 'luano' in current_firstname:
                agent_name = "Luano van Eck"
                agent_title = "Developer"
            elif 'omega' in current_username:
                agent_name = "Omega System Assistant"
                agent_title = "Automated System"

            signature_context = {
                'request': request,
                'agent_name': agent_name,
                'agent_title': agent_title,
                'logo_url': 'https://acvv.futurasa.co.za/static/images/futura_logo.png'
            }
            signature_html = render_to_string('acvv_app/acvv_email_signature.html', signature_context)

            # Insert signature between the user's new reply and whatever quoted thread they chose to keep
            reply_style = "font-family: 'Century Gothic', Arial, sans-serif; font-size: 11pt; color: #000000; line-height: 1.5;"
            thread_marker = '<div data-thread-divider="true"'
            if thread_marker in formatted_body:
                reply_part, thread_part = formatted_body.split(thread_marker, 1)
                full_html_body = f'<div style="{reply_style}">{reply_part}</div><br>{signature_html}<br>{thread_marker}{thread_part}'
            else:
                full_html_body = f'<div style="{reply_style}">{formatted_body}</div><br>{signature_html}'

            attachments_list = request.FILES.getlist('email_attachments')
            selected_action_type = request.POST.get('action_log_type') or "Correspondence"

            result = OutlookGraphService.send_outlook_email(
                target_email,
                recipient,
                subject,
                full_html_body,
                content_type='Html',
                attachments=attachments_list,
                cc=reply_cc,
                bcc=reply_bcc,
                user=None
            )

            if result.get('success'):
                sent_now = timezone.now()
                new_ms_id = f"REPLY-{delegation.pk}-{int(sent_now.timestamp())}"

                # Save ALL attachments + clean RFC822 .eml to local disk
                eml_rel_path, saved_atts = save_outgoing_email_locally(
                    owner_key=new_ms_id,
                    subject=subject,
                    sender=target_email,
                    recipient=recipient,
                    html_body=full_html_body,
                    cc=reply_cc,
                    bcc=reply_bcc,
                    uploaded_files=attachments_list,
                    sent_dt=sent_now,
                )

                # Save full sent thread + CC/BCC + .eml path in DelegationTransactionLog
                log_delegation_transaction(
                    delegation_id,
                    request.user,
                    subject,
                    recipient,
                    action_type='EMAIL_REPLY',
                    body=full_html_body,
                    cc_recipients=reply_cc,
                    bcc_recipients=reply_bcc,
                    eml_file_path=eml_rel_path,
                )

                EmailDelegation.objects.create(
                    email_id=new_ms_id,
                    subject=(subject or '(No Subject)')[:255],
                    body=full_html_body,
                    sender_address=target_email,
                    sender_name=request.user.get_full_name() or request.user.username,
                    to_recipients=recipient,
                    cc_recipients=reply_cc,
                    bcc_recipients=reply_bcc,
                    assigned_user=request.user,
                    status='SENT',
                    mip_names=delegation.mip_names,
                    email_category=f"PARENT:{delegation.pk}",
                    received_at=sent_now,
                    delegated_at=sent_now,
                    work_related=True,
                    communication_type='Reply',
                    has_attachments=bool(saved_atts),
                    eml_file_path=eml_rel_path,
                    is_fully_synced=True,
                )

                cc_note_segment = f"\nCC: {reply_cc}" if reply_cc else ""
                bcc_note_segment = f"\nBCC: {reply_bcc}" if reply_bcc else ""

                acvv_rec = Globalacvv.objects.filter(
                    Q(mip_names=delegation.mip_names) | Q(branch_code=delegation.mip_names)
                ).first()
                if acvv_rec:
                    ClientNotes.objects.create(
                        acvv_record=acvv_rec,
                        notes=f"Reply Sent: {subject}\nRecipient: {recipient}{cc_note_segment}{bcc_note_segment}",
                        user=request.user.username,
                        date=sent_now,
                        communication_type="Email",
                        action_note_type=selected_action_type
                    )

                messages.success(request, "Reply sent and archived locally.")
            else:
                messages.error(request, f"Reply failed: {result.get('error')}")
            return redirect('outlook_delegated_action', delegation_id=delegation_id)

    # --- 100% LOCAL DATA FOR GET ---
    acvv_records = Globalacvv.objects.all().only('mip_names', 'branch_code')
    attachments = _get_local_attachments_for_email(delegation.email_id, getattr(delegation, 'attachment', None))

    email_data = {
        'subject': delegation.subject or '(No Subject)',
        'body': {'content': delegation.body or 'No email content available locally.'},
        'from': {
            'emailAddress': {
                'name': delegation.sender_name or delegation.sender_address or 'Unknown',
                'address': delegation.sender_address or target_email,
            }
        },
        'to': delegation.to_recipients or target_email,
        'cc': delegation.cc_recipients or '-',
        'bcc': delegation.bcc_recipients or '-',
        'receivedDateTime': delegation.received_at,
    }

    # --- BUILD EDITABLE QUOTED THREAD FOR GET ---
    quoted_thread_html = ""
    if (delegation.body or '').strip():
        sent_date = delegation.received_at.strftime('%d %B %Y %H:%M') if delegation.received_at else 'Unknown'
        sender_name = delegation.sender_name or delegation.sender_address or 'Unknown'
        sender_addr = delegation.sender_address or 'Unknown'
        to_addresses = delegation.to_recipients or target_email
        orig_subject = delegation.subject or ''

        quoted_thread_html = f"""
        <div data-thread-divider="true" style="border:none; border-top:solid #B5C4DF 1.0pt; padding:6px 0 0 0; margin-top:16px;">
            <p style="margin:0; font-size:11.0pt; font-family:'Calibri',sans-serif; color:#333;">
                <b>From:</b> {sender_name} &lt;{sender_addr}&gt;<br>
                <b>Sent:</b> {sent_date}<br>
                <b>To:</b> {to_addresses}<br>
                <b>Subject:</b> {orig_subject}
            </p>
            <br>
            {delegation.body}
        </div>
        """

    context = {
        'delegation': delegation,
        'email': email_data,
        'attachments': attachments,
        'notes': delegation.notes.all().order_by('-created_at'),
        'acvv_records': acvv_records,
        'target_email': target_email,
        'quoted_thread_html': quoted_thread_html,
    }
    return render(request, 'acvv_app/outlook_delegated_action.html', context)

@login_required
def export_acvv_list_excel(request):
    """Exports filtered ACVV records to Excel with specific column mapping."""
    search_query = request.GET.get('search_query')
    records = Globalacvv.objects.all()

    if search_query:
        records = records.filter(
            Q(mip_names__icontains=search_query) |
            Q(branch_code__icontains=search_query) |
            Q(tel__icontains=search_query) |
            Q(tel_2__icontains=search_query)
        )
    
    records = records.order_by('mip_names')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ACVV Records Export"

    headers = [
        'Member Group Name', 'MG Code', 'Company Status', 
        'Last Recon - Status', 'Member Count', 'Last Recon - Date', 
        'Bill Amount', 'MG Contact Email', 'MG Contact Tel. 1', 'MG Contact Tel. 2'
    ]
    ws.append(headers)

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="43a047", end_color="43a047", fill_type="solid")
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill

    for record in records:
        ws.append([
            record.mip_names,                      # Member Group Name
            record.branch_code or "-",             # MG Code
            record.status or "-",                  # Company Status
            "",                                    # Last Recon - Status
            record.member or "-",                  # Member Count
            "",                                    # Last Recon - Date
            record.contribution_amount or "-",     # Bill Amount
            record.mg_email_address or "-",        # MG Contact Email
            record.tel or "-",                     # MG Contact Tel. 1
            record.tel_2 or "-"                    # UPDATED: MG Contact Tel. 2
        ])

    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except: pass
        ws.column_dimensions[column].width = max_length + 2

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="ACVV_Export_{datetime.now().strftime("%Y%m%d")}.xlsx"'
    wb.save(response)
    return response

@login_required
def acvv_list(request):
    """
    Displays a list of all ACVV records from the Globalacvv model with search functionality.
    Sorted by branch code. Handles creating a new ACVV client record via POST.
    """
    if request.method == 'POST':
        # Normalize email input to handle multiple addresses entered with commas or semicolons
        raw_emails = request.POST.get('mg_email_address', '')
        email_list = [e.strip() for e in raw_emails.replace(';', ',').split(',') if e.strip()]
        mg_email_address = ",".join(email_list)

        mip_names = request.POST.get('mip_names')
        branch_code = request.POST.get('branch_code')

        if not mip_names:
            messages.error(request, "Client/Branch Name (MIP Names) is required.")
            return redirect('acvv_list')

        # Check if record with this name already exists
        if Globalacvv.objects.filter(mip_names=mip_names).exists():
            messages.error(request, f"An ACVV record with the name '{mip_names}' already exists.")
            return redirect('acvv_list')

        # Create the new record capturing all fields
        new_record = Globalacvv.objects.create(
            mip_names=mip_names,
            branch_code=branch_code,
            member=request.POST.get('member', ''),
            contribution_amount=request.POST.get('contribution_amount', ''),
            tel=request.POST.get('tel', ''),
            tel_2=request.POST.get('tel_2', ''),
            mg_email_address=mg_email_address,
            bank=request.POST.get('bank', ''),
            branch=request.POST.get('branch', ''),
            account_number=request.POST.get('account_number', ''),
            account_name=request.POST.get('account_name', ''),
            account_type=request.POST.get('account_type', ''),
            employer_contacts=request.POST.get('employer_contacts', ''),
            mg_address=request.POST.get('mg_address', ''),
            npo_code=request.POST.get('npo_code', ''),
            mg_bank_info=request.POST.get('mg_bank_info', '')
        )
        
        messages.success(request, f"New ACVV client '{new_record.mip_names}' created successfully.")
        return redirect('acvv_information', mip_names=new_record.mip_names)

    acvv_records = Globalacvv.objects.all()
    search_query = request.GET.get('search_query')

    # Apply search filter (Updated to include Telephone numbers)
    if search_query:
        acvv_records = acvv_records.filter(
            Q(mip_names__icontains=search_query) |
            Q(branch_code__icontains=search_query) |
            Q(tel__icontains=search_query) |
            Q(tel_2__icontains=search_query)
        )

    # Order the results by branch code
    acvv_records = acvv_records.order_by('branch_code')

    context = {
        'acvv_records': acvv_records,
        'search_query': search_query or ''
    }
    return render(request, 'acvv_app/acvv_list.html', context)

@login_required
def acvv_information(request, mip_names):
    """
    Detailed view for a specific ACVV record with unified logging.
    Includes support for TEL, TEL 2, MG ADDRESS, NPO CODE, MG BANK INFO, 
    and the new BANK & EMPLOYER CONTACT fields from the Globalacvv model.
    """
    # 🔑 FIX: Look up the record by matching either 'mip_names' OR 'branch_code' 
    # to handle code-based routing links safely without throwing a 404.
    acvv_record = get_object_or_404(Globalacvv, Q(mip_names=mip_names) | Q(branch_code=mip_names))
    
    if request.method == 'POST':
        # 1. Handle Note Uploads
        if 'add_note' in request.POST:
            note_content = request.POST.get('internal_note_text')
            comm_type = request.POST.get('communication_type')
            action_note = request.POST.get('action_note_type')
            uploaded_file = request.FILES.get('note_attachment')

            if note_content or uploaded_file:
                file_url = None
                if uploaded_file:
                    fs = FileSystemStorage()
                    filename = fs.save(f"notes/{uploaded_file.name}", uploaded_file)
                    file_url = fs.url(filename)

                ClientNotes.objects.create(
                    acvv_record=acvv_record, 
                    notes=note_content,
                    user=request.user.username, 
                    date=timezone.now(),
                    communication_type=comm_type, 
                    action_note_type=action_note,
                    attachment=file_url
                )
                messages.success(request, "Internal note added.")
                return redirect(f'/acvv-records/{acvv_record.mip_names}/#notes-tab')

        # 2. Handle PDF uploads
        elif 'upload_pdf' in request.POST:
            pdf_file = request.FILES.get('branch_pdf')
            if pdf_file:
                fs = FileSystemStorage()
                path = f"branch_docs/{acvv_record.mip_names}/{pdf_file.name}"
                filename = fs.save(path, pdf_file)
                file_url = fs.url(filename)
                BranchDocument.objects.create(
                    branch_name=acvv_record.mip_names, 
                    file_name=pdf_file.name,
                    file_path=file_url, 
                    uploaded_by=request.user.username
                )
                messages.success(request, "PDF added.")
                return redirect(f'/acvv-records/{acvv_record.mip_names}/#pdf-upload')

        # 3. Handle Contact Info Update (UPDATED: Matched exact HTML name attributes)
        elif 'update_contact_info' in request.POST:
            # Normalize email input to handle multiple addresses entered with commas or semicolons
            raw_emails = request.POST.get('mg_email_address', '')
            # Clean: Replace ; with , then split, strip whitespace, and rejoin with comma
            email_list = [e.strip() for e in raw_emails.replace(';', ',').split(',') if e.strip()]
            acvv_record.mg_email_address = ",".join(email_list)
            
            # --- EXTRACT AND SAVE ALL DATA MATCHING THE HTML NAMES ---
            acvv_record.branch_code = request.POST.get('branch_code')
            acvv_record.member = request.POST.get('member')
            acvv_record.contribution_amount = request.POST.get('contribution_amount')
            
            acvv_record.tel = request.POST.get('tel')
            acvv_record.tel_2 = request.POST.get('tel_2')
            
            acvv_record.bank = request.POST.get('bank')
            acvv_record.branch = request.POST.get('branch')
            acvv_record.account_number = request.POST.get('account_number')
            acvv_record.account_name = request.POST.get('account_name')
            acvv_record.account_type = request.POST.get('account_type')
            acvv_record.employer_contacts = request.POST.get('employer_contacts')
            
            acvv_record.mg_address = request.POST.get('mg_address')
            acvv_record.npo_code = request.POST.get('npo_code')
            acvv_record.mg_bank_info = request.POST.get('mg_bank_info')
            
            acvv_record.save()
            messages.success(request, "Contact information updated successfully.")
            return redirect('acvv_information', mip_names=acvv_record.mip_names)

    # --- DATA FETCHING & COLUMN LINKING ---
    all_notes = ClientNotes.objects.filter(acvv_record=acvv_record)
    
    notes = all_notes.order_by('-date')
    
    company_claims = AcvvClaim.objects.filter(company_code=mip_names).order_by('-claim_created_date')
    branch_docs = BranchDocument.objects.filter(branch_name=mip_names).order_by('-uploaded_at')

    delegated_logs = EmailDelegation.objects.filter(
        Q(mip_names__icontains=acvv_record.mip_names) | Q(mip_names__icontains=acvv_record.branch_code)
    ).select_related('assigned_user')

    # --- 1. BUILD LOOKUP FOR REAL-TIME ACTION TYPES FROM CLIENT_NOTES ---
    notes_action_map = {}
    for n in all_notes:
        note_text = n.notes or ""
        if "Email Sent:" in note_text:
            try:
                sub_line = note_text.split('\n')[0].replace("Email Sent:", "").strip()
                notes_action_map[sub_line] = n.action_note_type
            except Exception:
                pass

    # --- 2. FETCH AND MAP REMARKS CONTENT FROM DELEGATION_NOTE TABLE ---
    delegation_ids = delegated_logs.values_list('id', flat=True)
    
    raw_delegation_notes = DelegationNote.objects.filter(
        delegation_id__in=delegation_ids
    ).order_by('created_at')

    delegation_notes_map = {}
    for d_note in raw_delegation_notes:
        if d_note.delegation_id not in delegation_notes_map:
            delegation_notes_map[d_note.delegation_id] = []
        
        formatted_entry = f"[{d_note.created_at.strftime('%Y-%m-%d')}] {d_note.content}"
        delegation_notes_map[d_note.delegation_id].append(formatted_entry)

    combined_email_log = []
    for log in delegated_logs:
        if log.status == 'SENT' or log.status == 'COM':
            raw_comm_type = getattr(log, 'communication_type', '') or ''
            comm_type_lower = raw_comm_type.lower()
            
            if comm_type_lower == 'reply':
                log_type = 'REPLY'
                log_icon = '↩️'
                badge_color = '#f7931e'
            elif comm_type_lower == 'claim sent':
                log_type = 'CLAIM SENT'
                log_icon = '📋'
                badge_color = '#9c27b0'
            elif comm_type_lower == 'two pot email':
                log_type = 'TWO POT EMAIL'
                log_icon = '🍯'
                badge_color = '#e65100'
            else:
                log_type = 'DIRECT'
                log_icon = '📤'
                badge_color = '#28a745'
        else:
            log_type = 'ORIGINAL'
            log_icon = '📩'
            badge_color = '#1976d2' if log.status != 'DLT' else '#ef5350'

        resolved_action_note_type = notes_action_map.get(log.subject, getattr(log, 'action_note_type', None))
        if not resolved_action_note_type or resolved_action_note_type == 'None':
            resolved_action_note_type = '-'

        matched_notes_list = delegation_notes_map.get(log.id, [])
        resolved_delegation_content = " | ".join(matched_notes_list) if matched_notes_list else "-"

        combined_email_log.append({
            'type': log_type,
            'icon': log_icon,
            'badge_color': badge_color, 
            'sender_address': getattr(log, 'sender_address', '-'),  # 🔑 ADD THIS LINE
            'subject': log.subject or "Outlook Task",
            'received_at': log.received_at,
            'assigned_to': log.assigned_user.username if log.assigned_user else "Unassigned",
            'display_type': log_type if log.status == 'SENT' else log.get_status_display(),
            'email_id': log.email_id,
            'file_url': log.attachment.url if hasattr(log, 'attachment') and log.attachment else None,
            'action_note_type': resolved_action_note_type,
            'delegation_note_content': resolved_delegation_content, 
            'sort_date': log.received_at or log.delegated_at
        })

    combined_email_log.sort(key=lambda x: x['sort_date'] if x['sort_date'] else timezone.datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    context = {
        'acvv_record': acvv_record,
        'combined_email_log': combined_email_log, 
        'notes': notes,
        'company_claims': company_claims,
        'branch_docs': branch_docs,
        'my_delegated_emails': EmailDelegation.objects.filter(assigned_user=request.user, status='DEL'),
    }
    return render(request, 'acvv_app/acvv_information.html', context)

@login_required
def outlook_delegate_to(request, email_id):
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    available_users = User.objects.filter(is_active=True).order_by('username')
    acvv_records = Globalacvv.objects.all().values('mip_names', 'branch_code')

    # 1. Load 100% locally (ingest once from Graph only if not yet synced; NEVER delete on 404)
    delegation = EmailDelegation.objects.filter(email_id=email_id).first()
    if not delegation:
        delegation = ingest_single_email_from_graph(email_id, target_email=target_email)
        if not delegation:
            messages.error(request, "Could not locate this email locally or in Outlook.")
            return redirect('outlook_dashboard')
    else:
        delegation = _ensure_local_email_data(delegation, target_email=target_email)

    attachments = _get_local_attachments_for_email(delegation.email_id, getattr(delegation, 'attachment', None))
    email_subject = delegation.subject or '(No Subject)'
    sender_email = delegation.sender_address or ''
    sender_name = delegation.sender_name or sender_email or 'Unknown'

    if request.method == 'POST':
        try:
            with transaction.atomic():
                work_related_raw = request.POST.get('work_related')
                is_work_related = (work_related_raw == 'Yes')
                assignee_pk = request.POST.get('agent_name')
                mip_names_value = request.POST.get('mip_names')
                action_log_type_value = request.POST.get('action_log_type', 'General')

                if not is_work_related:
                    delegation.work_related = False
                    delegation.status = 'DLT'
                    delegation.mip_names = mip_names_value
                    delegation.assigned_user = None
                    delegation.save(update_fields=['work_related', 'status', 'mip_names', 'assigned_user'])
                    messages.success(request, "Task moved to Recycle Bin.")
                    return redirect('outlook_dashboard')

                else:
                    if assignee_pk and assignee_pk not in ['', '__Select Agent__']:
                        target_assignee = get_object_or_404(User, pk=assignee_pk)

                        delegation.assigned_user = target_assignee
                        delegation.mip_names = mip_names_value
                        delegation.email_category = request.POST.get('email_category')
                        delegation.work_related = True
                        delegation.status = 'DEL'
                        delegation.delegated_at = timezone.now()
                        delegation.communication_type = request.POST.get('email_method', 'Email')
                        delegation.save(update_fields=[
                            'assigned_user', 'mip_names', 'email_category',
                            'work_related', 'status', 'delegated_at', 'communication_type'
                        ])

                        acvv_rec = Globalacvv.objects.filter(
                            Q(mip_names=mip_names_value) | Q(branch_code=mip_names_value)
                        ).first()
                        if acvv_rec:
                            ClientNotes.objects.create(
                                acvv_record=acvv_rec,
                                notes=f"Email delegated to {target_assignee.username}",
                                user=request.user.username,
                                date=timezone.now(),
                                communication_type="Email Delegation",
                                action_note_type=action_log_type_value
                            )

                        messages.success(request, f"Task successfully assigned to {target_assignee.username}!")
                        return redirect('outlook_dashboard')
                    else:
                        messages.error(request, "Please select an agent.")

        except Exception as e:
            logger.exception(f"Delegation error for ID {email_id}")
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('outlook_dashboard')

    context = {
        'delegation': delegation,
        'email_id': email_id,
        'email_subject': email_subject,
        'email_sender': sender_email,
        'email_sender_name': sender_name,
        'email_to': delegation.to_recipients or target_email,
        'email_cc': delegation.cc_recipients or '-',
        'email_bcc': delegation.bcc_recipients or '-',
        'email_received_at': delegation.received_at,
        'email_content': delegation.body or '',
        'attachments': attachments,
        'available_users': available_users,
        'acvv_records': acvv_records,
    }
    return render(request, 'acvv_app/outlook_delegate_to.html', context)

@login_required
def outlook_email_content(request, email_id):
    """
    Renders the raw HTML content of an email 100% locally for iframe display.
    """
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    delegation = EmailDelegation.objects.filter(email_id=email_id).first()
    if delegation:
        delegation = _ensure_local_email_data(delegation, target_email=target_email)
        content = delegation.body or 'No email body found.'
    else:
        content = 'Email content not found locally.'

    wrapped_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>body {{ font-family: sans-serif; margin: 15px; }}</style>
    </head>
    <body>
        {content}
    </body>
    </html>
    """
    return HttpResponse(wrapped_content, content_type='text/html')

@login_required
def save_acvv_claim(request, company_code):
    """
    Handles Member Claim registration and updates ONLY.
    No longer contains any email-sending logic.
    """
    if request.method == 'POST':
        id_number = request.POST.get('id_number')
        
        # Only proceed if we actually have claim data
        if id_number:
            claim_id = request.POST.get('claim_id')
            data = {
                'company_code': company_code,
                'id_number': id_number,
                'member_name': request.POST.get('member_name'),
                'member_surname': request.POST.get('member_surname'),
                'mip_number': request.POST.get('mip_number'),
                'claim_type': request.POST.get('claim_type'),
                'exit_reason': request.POST.get('exit_reason'),
                'claim_allocation': request.POST.get('claim_allocation'),
                'claim_status': request.POST.get('claim_status'),
                'payment_option': request.POST.get('payment_option'),
                'claim_amount': request.POST.get('claim_amount') or None,
                'claim_created_date': request.POST.get('claim_created_date') or None,
                'last_contribution_date': request.POST.get('last_contribution_date') or None,
                'date_submitted': request.POST.get('date_submitted') or None,
                'date_paid': request.POST.get('date_paid') or None,
                'vested_pot_available': request.POST.get('vested_pot_available') == 'on',
                'vested_pot_paid_date': request.POST.get('vested_pot_paid_date') or None,
                'savings_pot_available': request.POST.get('savings_pot_available') == 'on',
                'savings_pot_paid_date': request.POST.get('savings_pot_paid_date') or None,
                'infund_cert_date': request.POST.get('infund_cert_date') or None,
                'linked_email_id': request.POST.get('linked_email_id'),
            }

            if claim_id:
                AcvvClaim.objects.filter(id=claim_id).update(**data)
                claim_instance = AcvvClaim.objects.get(id=claim_id)
                messages.success(request, "Claim updated successfully.")
            else:
                claim_instance = AcvvClaim.objects.create(**data)
                messages.success(request, "New claim created successfully.")

            # Note/Attachment logic for the claim record itself
            note_selection = request.POST.get('note_selection')
            note_description = request.POST.get('note_description')
            claim_file = request.FILES.get('claim_attachment')
            if note_selection or note_description or claim_file:
                claim_instance.notes.create(
                    note_selection=note_selection,
                    note_description=note_description,
                    attachment=claim_file,
                    created_by=request.user
                )
        else:
            messages.warning(request, "Claim save ignored: No ID Number provided.")

    return redirect('acvv_information', mip_names=company_code)

@login_required
def global_two_pot_view(request):
    """Dedicated Register for ONLY Two Pot claims with Note/Attachment support."""
    query = request.GET.get('q')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # --- HARD FILTER: Only Two Pot ---
    base_claims = AcvvClaim.objects.filter(claim_type='Two Pot').prefetch_related('notes').order_by('-claim_created_date')

    if query:
        base_claims = base_claims.filter(
            Q(id_number__icontains=query) | 
            Q(member_surname__icontains=query) | 
            Q(company_code__icontains=query)
        )

    if start_date and end_date:
        base_claims = base_claims.filter(claim_created_date__range=[parse_date(start_date), parse_date(end_date)])

    # Pagination
    paginator = Paginator(base_claims, 200) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 100% Local Email Preview Logic (Zero live Graph API calls)
    delegation_pks = [c.linked_email_id for c in page_obj if c.linked_email_id]
    if delegation_pks:
        numeric_pks = [int(pk) for pk in delegation_pks if str(pk).isdigit()]
        delegations_map = EmailDelegation.objects.in_bulk(numeric_pks)

        for claim in page_obj:
            if claim.linked_email_id and str(claim.linked_email_id).isdigit():
                del_obj = delegations_map.get(int(claim.linked_email_id))
                if del_obj:
                    claim.email_preview_subject = del_obj.subject
                    claim.email_preview_sender = del_obj.sender_address
                    claim.email_preview_body = del_obj.body or del_obj.snippet or ''
                    claim.email_preview_date = del_obj.received_at

    return render(request, 'acvv_app/two_pot_global.html', {
        'page_obj': page_obj, 
        'claims': page_obj,
        'all_companies': Globalacvv.objects.values('mip_names', 'branch_code'),
        'my_delegated_emails': EmailDelegation.objects.filter(assigned_user=request.user, status='DEL').order_by('-received_at'),
        'is_two_pot_view': True,
        'search_query': query,
        'start_date': start_date,
        'end_date': end_date,
    })
    
@login_required
def global_claims_view(request):
    """Register for ALL claims EXCEPT Two Pot."""
    query = request.GET.get('q')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    base_claims = AcvvClaim.objects.exclude(claim_type='Two Pot')

    if query:
        base_claims = base_claims.filter(
            Q(id_number__icontains=query) | 
            Q(member_surname__icontains=query) | 
            Q(company_code__icontains=query)
        )

    if from_date:
        base_claims = base_claims.filter(claim_created_date__gte=from_date)
    if to_date:
        base_claims = base_claims.filter(claim_created_date__lte=to_date)

    claims_list = base_claims.order_by('-claim_created_date')

    # Pagination (36 claims per page)
    paginator = Paginator(claims_list, 36) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    current_page_claims = page_obj.object_list

    # 100% Local Email Preview Logic (Zero live Graph API calls)
    delegation_ids = [str(c.linked_email_id) for c in current_page_claims if c.linked_email_id]
    if delegation_ids:
        delegations_map = EmailDelegation.objects.in_bulk(delegation_ids, field_name='email_id')

        for claim in current_page_claims:
            if claim.linked_email_id:
                del_obj = delegations_map.get(str(claim.linked_email_id))
                if del_obj:
                    claim.email_preview_subject = del_obj.subject
                    claim.email_preview_sender = del_obj.sender_address
                    claim.email_preview_body = del_obj.body or del_obj.snippet or ''
                    claim.email_preview_date = del_obj.received_at

    return render(request, 'acvv_app/global_claims.html', {
        'claims': current_page_claims,
        'page_obj': page_obj,
        'all_companies': Globalacvv.objects.values('mip_names', 'branch_code'),
        'my_delegated_emails': EmailDelegation.objects.filter(assigned_user=request.user).exclude(status='DLT'),
        'is_two_pot_view': False 
    })

@login_required
def save_global_claim(request):
    """Unified save view with note handling, file attachments, and locally archived outgoing emails."""
    if request.method == 'POST':
        claim_id = request.POST.get('claim_id')
        claim_type = request.POST.get('claim_type') 
        company_code = request.POST.get('company_code')
        linked_id = request.POST.get('linked_email_id') or None

        claim_amount_raw = request.POST.get('claim_amount')
        claim_amount_val = None
        if claim_amount_raw and claim_amount_raw.strip():
            try:
                claim_amount_val = float(claim_amount_raw.replace(',', '').strip())
            except ValueError:
                pass

        def clean_date_input(val):
            if val and val.strip() and val.strip() != 'None' and val.strip() != '':
                return val.strip()
            return None

        form_qualified = request.POST.get('qualified') or "YES"
        form_date_submitted = clean_date_input(request.POST.get('date_submitted'))
        form_informed_er = request.POST.get('informed_er') or "NO"

        form_submitted_by_agent = request.POST.get('agent')
        if not form_submitted_by_agent:
            current_username = request.user.username.lower()
            current_firstname = request.user.first_name.lower() if request.user.first_name else ""
            if 'jesica' in current_username or 'jessica' in current_username or 'jesica' in current_firstname or 'jessica' in current_firstname:
                form_submitted_by_agent = "JH"
            elif 'timothy' in current_username or 'timothy' in current_firstname:
                form_submitted_by_agent = "TD"

        vested_pot_available = request.POST.get('vested_pot_available') == 'on'
        savings_pot_available = request.POST.get('savings_pot_available') == 'on'
        vested_pot_paid_date = clean_date_input(request.POST.get('vested_pot_paid_date'))
        savings_pot_paid_date = clean_date_input(request.POST.get('savings_pot_paid_date'))
        infund_cert_date = clean_date_input(request.POST.get('infund_cert_date'))

        data = {
            'company_code': company_code,
            'agent': form_submitted_by_agent, 
            'id_number': request.POST.get('id_number'),
            'member_name': request.POST.get('member_name'),
            'member_surname': request.POST.get('member_surname'),
            'mip_number': request.POST.get('mip_number'),
            'claim_type': claim_type,
            'claim_status': request.POST.get('claim_status'),
            'payment_option': request.POST.get('payment_option'),
            'exit_reason': request.POST.get('exit_reason'),
            'claim_allocation': request.POST.get('claim_allocation') or "New Claim",
            'claim_amount': claim_amount_val,
            'claim_created_date': clean_date_input(request.POST.get('claim_created_date')),
            'date_submitted': form_date_submitted,
            'last_contribution_date': clean_date_input(request.POST.get('last_contribution_date')),
            'date_paid': clean_date_input(request.POST.get('date_paid')),
            'linked_email_id': linked_id,
            'vested_pot_available': vested_pot_available,
            'savings_pot_available': savings_pot_available,
            'vested_pot_paid_date': vested_pot_paid_date,
            'savings_pot_paid_date': savings_pot_paid_date,
            'infund_cert_date': infund_cert_date,
        }

        # 1. SAVE OR UPDATE THE CLAIM
        claim_obj = None
        try:
            if claim_id and claim_id.strip():
                AcvvClaim.objects.filter(id=claim_id).update(**data)
                claim_obj = AcvvClaim.objects.get(id=claim_id)
                messages.success(request, f"Claim for {claim_obj.member_surname} updated.")
            else:
                claim_obj = AcvvClaim.objects.create(**data)
                messages.success(request, f"New {claim_type} claim created successfully.")
        except Exception as e:
            logger.error(f"Critical database save error: {str(e)}")
            messages.error(request, f"Database Save Failed: {str(e)}")
            if claim_type == 'Two Pot':
                return redirect('global_two_pot')
            return redirect('global_claims')

        # 2. HANDLE CLAIM NOTES & INTERNAL ATTACHMENTS
        note_selection = request.POST.get('note_selection')
        note_description = request.POST.get('note_description') or ""
        internal_attachment = request.FILES.get('claim_attachment')

        tracking_metadata_summary = (
            f"\n\n[Tracking Parameters Logged]:\n"
            f"- Qualified: {form_qualified}\n"
            f"- Date Submitted Online: {form_date_submitted or 'N/A'}\n"
            f"- Informed ER: {form_informed_er}\n"
            f"- Submitted by Agent: {form_submitted_by_agent or 'N/A'}"
        )
        enriched_note_details = note_description + tracking_metadata_summary

        if claim_obj:
            try:
                resolved_note_selection = note_selection if note_selection else "TRACKING METADATA UPDATE"
                ClaimNote.objects.create(
                    claim=claim_obj,
                    note_selection=resolved_note_selection,
                    note_description=enriched_note_details,
                    attachment=internal_attachment,
                    created_by=request.user
                )
                messages.info(request, "Internal claim note saved.")
            except Exception as note_err:
                logger.warning(f"Non-critical note save error: {str(note_err)}")

        # 3. HANDLE OUTGOING EMAIL LOGIC WITH LOCAL MULTI-ATTACHMENT & .EML ARCHIVAL
        recipient = request.POST.get('member_recipient_email')
        subject = request.POST.get('member_email_subject_reply')
        body = request.POST.get('email_body_html_content')
        email_attachments = request.FILES.getlist('email_attachment')

        if recipient and subject and body:
            target_email = settings.OUTLOOK_EMAIL_ADDRESS

            current_username = request.user.username.lower()
            current_firstname = request.user.first_name.lower() if request.user.first_name else ""

            agent_name = request.user.get_full_name() or request.user.username.replace('_', ' ').title()
            agent_title = "Administrator"

            if 'timothy' in current_username or 'timothy' in current_firstname:
                agent_name = "Timothy Davids"
                agent_title = "Indexing Specialist"
            elif 'jesica' in current_username or 'jessica' in current_username or 'jesica' in current_firstname:
                agent_name = "Jesica Haynes"
                agent_title = "Reconciliations Specialist"
            elif 'luanovaneck' in current_username or 'luano' in current_firstname:
                agent_name = "Luano van Eck"
                agent_title = "Developer"
            elif 'omega' in current_username:
                agent_name = "Omega System Assistant"
                agent_title = "Automated System"

            signature_context = {
                'request': request,
                'agent_name': agent_name,
                'agent_title': agent_title,
                'logo_url': 'https://acvv.futurasa.co.za/static/images/futura_logo.png'
            }
            signature_html = render_to_string('acvv_app/acvv_email_signature.html', signature_context)
            full_html_body = f"<div>{body}</div><br><br>{signature_html}"

            result = OutlookGraphService.send_outlook_email(
                target_email,
                recipient,
                subject,
                full_html_body,
                content_type='Html',
                attachments=email_attachments,
                user=None
            )

            if result.get('success'):
                sent_now = timezone.now()
                acvv_record = Globalacvv.objects.filter(
                    Q(mip_names=company_code) | Q(branch_code=company_code)
                ).first()

                resolved_mip_name = acvv_record.mip_names if acvv_record else company_code
                note_selection_type = note_selection if note_selection else "Correspondence"
                resolved_comm_type = 'Two Pot Email' if claim_type == 'Two Pot' else 'Claim Sent'
                new_ms_id = f"CLAIM-{int(sent_now.timestamp())}-{request.user.id}"

                try:
                    eml_rel_path, saved_atts = save_outgoing_email_locally(
                        owner_key=new_ms_id,
                        subject=subject,
                        sender=target_email,
                        recipient=recipient,
                        html_body=full_html_body,
                        uploaded_files=email_attachments,
                        sent_dt=sent_now,
                    )

                    EmailDelegation.objects.create(
                        email_id=new_ms_id,
                        subject=(subject or '(No Subject)')[:255],
                        body=full_html_body,
                        sender_address=target_email,
                        sender_name=agent_name,
                        to_recipients=recipient,
                        assigned_user=request.user,
                        status='SENT',
                        mip_names=resolved_mip_name,
                        received_at=sent_now,
                        delegated_at=sent_now,
                        work_related=True,
                        communication_type=resolved_comm_type,
                        has_attachments=bool(saved_atts),
                        eml_file_path=eml_rel_path,
                        is_fully_synced=True,
                    )

                    if acvv_record:
                        att_names = ", ".join([a.name for a in saved_atts])
                        att_suffix = f" (with attachment: {att_names})" if att_names else ""
                        ClientNotes.objects.create(
                            acvv_record=acvv_record,
                            notes=f"Email Sent: {subject}\nRecipient: {recipient}{att_suffix}",
                            user=request.user.username,
                            date=sent_now,
                            communication_type="Email",
                            action_note_type=note_selection_type
                        )
                except Exception as log_err:
                    logger.error(f"Non-critical claim email log error: {log_err}")

                messages.success(request, f"Email sent successfully to {recipient}.")
            else:
                messages.error(request, f"Email failed: {result.get('error')}")

        # Final Redirects
        if claim_type == 'Two Pot':
            return redirect('global_two_pot')
        return redirect('global_claims')

@login_required
def export_global_claims_excel(request):
    """
    Exports claims to the standard Register format (Green Theme) matching the attachment.
    Excludes 'Two Pot' claims. Includes newly added Pot fields and Last Contribution Date.
    """
    query = request.GET.get('q')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    # 1. Fetch claims excluding 'Two Pot'
    claims = AcvvClaim.objects.all().exclude(claim_type='Two Pot').order_by('claim_created_date')
    
    if query:
        claims = claims.filter(
            Q(id_number__icontains=query) | 
            Q(member_surname__icontains=query) | 
            Q(company_code__icontains=query)
        )

    # --- NEW: Apply Date Range Filters to Excel Export ---
    if from_date:
        claims = claims.filter(claim_created_date__gte=from_date)
    if to_date:
        claims = claims.filter(claim_created_date__lte=to_date)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Claims Register"

    # Define Green Theme Styles (Matching the provided image)
    green_fill = PatternFill(start_color="92D050", end_color="92D050", fill_type="solid")
    
    # Standard thin borders for all cells
    border = Border(left=Side(style='thin', color='000000'), 
                    right=Side(style='thin', color='000000'), 
                    top=Side(style='thin', color='000000'), 
                    bottom=Side(style='thin', color='000000'))
                    
    header_font = Font(bold=True, size=11, color="000000")
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    data_alignment = Alignment(vertical='center')

    # 2. Header Row Titles (Added 'Last Contribution Date')
    headers = [
        'Co.Code', 'Branch', 'Agent', 'MIP Number', 'ID Number', 
        'Name', 'Surname', 'Type', 'Status', 'Exit Reason', 
        'Last Contribution Date', 'Created', 'Submitted', 'Paid', 'Last Reconciled', 'Claim Allocation',
        'Vested Pot Available', 'Vested Pot Paid Date', 
        'Savings Pot Available', 'Savings Pot Paid Date', 
        'In-Fund Cert Date'
    ]
    
    ws.append(headers)
    
    # Apply styling to headers
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = green_fill
        cell.alignment = header_alignment
        cell.border = border

    # Freeze the top row so headers stay visible when scrolling down
    ws.freeze_panes = "A2"

    # 3. Data Rows
    for c in claims:
        row = [
            c.company_code,                                              # Co Code
            '',                                                          # Branch
            c.agent if hasattr(c, 'agent') else '',                      # Agent
            c.mip_number if hasattr(c, 'mip_number') else '',            # MIP Number
            c.id_number,                                                 # ID Number
            c.member_name,                                               # Name
            c.member_surname,                                            # Surname
            c.claim_type,                                                # Type
            c.claim_status,                                              # Status
            c.exit_reason if hasattr(c, 'exit_reason') else '',          # Exit Reason
            
            # --- NEW MISSING FIELD ADDED HERE ---
            c.last_contribution_date.strftime('%Y-%m-%d') if getattr(c, 'last_contribution_date', None) else '', 
            
            c.claim_created_date.strftime('%Y-%m-%d') if c.claim_created_date else '', # Created
            c.date_submitted.strftime('%Y-%m-%d') if getattr(c, 'date_submitted', None) else '', # Submitted
            c.date_paid.strftime('%Y-%m-%d') if getattr(c, 'date_paid', None) else '',              # Paid
            c.last_reconciled.strftime('%Y-%m-%d') if getattr(c, 'last_reconciled', None) else '', # Last Reconciled
            c.claim_allocation if hasattr(c, 'claim_allocation') else '',        # Claim Allocation
            
            # --- NEW POT FIELDS ---
            'Yes' if getattr(c, 'vested_pot_available', False) else 'No',        # Vested Pot Available
            c.vested_pot_paid_date.strftime('%Y-%m-%d') if getattr(c, 'vested_pot_paid_date', None) else '', # Vested Paid Date
            'Yes' if getattr(c, 'savings_pot_available', False) else 'No',       # Savings Pot Available
            c.savings_pot_paid_date.strftime('%Y-%m-%d') if getattr(c, 'savings_pot_paid_date', None) else '', # Savings Paid Date
            c.infund_cert_date.strftime('%Y-%m-%d') if getattr(c, 'infund_cert_date', None) else '',         # In-Fund Cert Date
        ]
        ws.append(row)
        
        # Apply borders and alignment to the data row
        for cell in ws[ws.max_row]:
            cell.border = border
            cell.alignment = data_alignment

    # Apply AutoFilter to the header row
    ws.auto_filter.ref = f"A1:{openpyxl.utils.get_column_letter(len(headers))}{ws.max_row}"

    # 4. Formatting - Auto-adjust Column Widths (Added an extra '15' for the new column)
    column_widths = [12, 15, 15, 15, 18, 15, 15, 12, 15, 15, 15, 12, 12, 12, 15, 20, 18, 18, 18, 18, 18]
    for i, width in enumerate(column_widths):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i+1)].width = width

    # Final response
    now = timezone.now()
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="Claims_Register_{now.strftime("%Y-%m-%d")}.xlsx"'
    wb.save(response)
    
    return response

@login_required
def recycle_bin_view(request):
    """Displays items marked as 'Deleted' (DLT) 100% locally from MySQL."""
    if request.user.username.lower() != 'omega' and not request.user.is_superuser:
        messages.error(request, "Access restricted.")
        return redirect('dashboard')

    recycled_items = EmailDelegation.objects.filter(
        status='DLT',
        work_related=False
    ).order_by('-received_at')

    tasks = []
    for item in recycled_items:
        tasks.append({
            'delegation_id': item.pk,
            'subject': item.subject or '(No Subject)',
            'from': item.sender_name or item.sender_address or 'Unknown',
            'received': item.received_at
        })

    return render(request, 'acvv_app/recycle_bin.html', {'tasks': tasks})

    return render(request, 'acvv_app/recycle_bin.html', {'tasks': tasks})

@login_required
def delete_recycled_item(request, delegation_id):
    """Permanently removes an item from the local database."""
    if request.user.username.lower() == 'omega' or request.user.is_superuser:
        item = get_object_or_404(EmailDelegation, pk=delegation_id)
        item.delete()
        messages.success(request, "Item permanently removed from Recycle Bin.")
    return redirect('recycle_bin')

@login_required
def restore_recycled_item(request, delegation_id):
    """
    Moves an item back to the Live Inbox.
    Resets status from 'DLT' back to 'NEW'.
    """
    if request.user.username.lower() == 'omega' or request.user.is_superuser:
        item = get_object_or_404(EmailDelegation, pk=delegation_id)
        item.work_related = True
        item.status = 'NEW'  # Resetting to NEW status
        item.save()
        messages.success(request, "Item restored to the Live Inbox.")
    return redirect('recycle_bin')

@login_required
def view_recycled_item(request, delegation_id):
    """View details of a recycled item 100% locally."""
    delegation = get_object_or_404(EmailDelegation, pk=delegation_id)
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    delegation = _ensure_local_email_data(delegation, target_email=target_email)

    email_data = {
        'subject': delegation.subject or '(No Subject)',
        'body': {'content': delegation.body or 'No content available locally.'},
        'from': {
            'emailAddress': {
                'name': delegation.sender_name or delegation.sender_address or 'Unknown',
                'address': delegation.sender_address or '',
            }
        },
        'receivedDateTime': delegation.received_at,
    }
    attachments = _get_local_attachments_for_email(delegation.email_id, getattr(delegation, 'attachment', None))

    return render(request, 'acvv_app/view_recycled_item.html', {
        'delegation': delegation,
        'email': email_data,
        'attachments': attachments,
    })

@login_required
def bulk_delete_recycled(request):
    """Handles multiple deletions based on DLT status."""
    if request.method == 'POST':
        item_ids = request.POST.getlist('selected_items')
        if 'empty_bin' in request.POST:
            # UPDATED: Bulk delete only items marked as DLT
            EmailDelegation.objects.filter(status='DLT').delete()
            messages.success(request, "Recycle Bin emptied.")
        elif item_ids:
            EmailDelegation.objects.filter(pk__in=item_ids, status='DLT').delete()
            messages.success(request, f"Deleted {len(item_ids)} items.")
    return redirect('recycle_bin')

@login_required
def outlook_view_thread(request, delegation_id):
    """
    100% locally rendered Email Thread Viewer:
    - Clicking View on DELEGATED (Original): Shows ONLY the original incoming email & its local attachments.
    - Clicking View on REPLY: Shows the original incoming email at the top, and the clean REPLY SENT & its attachments underneath.
    - Clicking View on DIRECT / CLAIM SENT / TWO POT EMAIL: Shows that outgoing email & its local attachments at the top.
    """
    if str(delegation_id).isdigit():
        clicked_task = get_object_or_404(EmailDelegation, Q(id=delegation_id) | Q(email_id=delegation_id))
    else:
        clicked_task = get_object_or_404(EmailDelegation, email_id=delegation_id)

    target_email = settings.OUTLOOK_EMAIL_ADDRESS

    def is_visually_empty(html_string):
        if not html_string:
            return True
        clean_text = re.sub(r'<[^>]+>', '', str(html_string)).replace('&nbsp;', '').strip()
        return len(clean_text) == 0

    def strip_quoted_thread(html_string):
        """Removes the appended Outlook quoted thread history from a reply body so only the reply itself is shown."""
        if not html_string:
            return ""
        parts = re.split(r'<div[^>]*border-top:\s*solid\s*#B5C4DF[^>]*>', str(html_string), maxsplit=1, flags=re.IGNORECASE)
        cleaned = parts[0]
        cleaned = re.sub(r'(\s*<br\s*/?>\s*)+$', '', cleaned, flags=re.IGNORECASE)
        return cleaned

    comm_type_lower = (clicked_task.communication_type or '').strip().lower()
    is_reply_row = (
        comm_type_lower == 'reply'
        or str(clicked_task.email_id).startswith('REPLY-')
    )

    # Resolve parent ORIGINAL incoming email when clicking View on a REPLY row
    parent_task = None
    if is_reply_row:
        if clicked_task.email_category and str(clicked_task.email_category).startswith('PARENT:'):
            parent_pk = str(clicked_task.email_category).replace('PARENT:', '').strip()
            if parent_pk.isdigit():
                parent_task = EmailDelegation.objects.filter(pk=int(parent_pk)).first()

        if not parent_task:
            tx_qs = DelegationTransactionLog.objects.filter(
                action_type='EMAIL_REPLY',
                subject=clicked_task.subject
            ).select_related('delegation').order_by('-transaction_time')
            for tx_cand in tx_qs:
                if tx_cand.delegation and tx_cand.delegation.status != 'SENT':
                    if clicked_task.received_at and tx_cand.transaction_time:
                        if abs((clicked_task.received_at - tx_cand.transaction_time).total_seconds()) <= 300:
                            parent_task = tx_cand.delegation
                            break
                    if not parent_task:
                        parent_task = tx_cand.delegation

        if not parent_task and clicked_task.mip_names:
            parent_task = EmailDelegation.objects.filter(
                mip_names=clicked_task.mip_names
            ).exclude(status='SENT').order_by('-received_at').first()

    main_task = parent_task if (is_reply_row and parent_task) else clicked_task
    main_is_local = (
        not main_task.email_id
        or str(main_task.email_id).strip().lower() == 'none'
        or any(str(main_task.email_id).startswith(p) for p in ['SENT-', 'LOCAL-', 'REPLY-', 'CLAIM-'])
    )
    main_is_outgoing = (main_task.status == 'SENT') or main_is_local

    # Ensure incoming main_task is hydrated locally once (no live Graph calls once synced)
    if not main_is_outgoing:
        main_task = _ensure_local_email_data(main_task, target_email=target_email)

    email_content = main_task.body or ''
    if main_is_outgoing and is_reply_row and not parent_task:
        email_content = strip_quoted_thread(email_content)

    if is_visually_empty(email_content):
        email_content = (
            "<div style='padding: 15px; background-color: #fff3cd; color: #856404; "
            "border: 1px solid #ffeeba; border-radius: 6px;'><strong>No Content Found:</strong> "
            "No local email body was found for this record.</div>"
        )

    attachments = _get_local_attachments_for_email(main_task.email_id, getattr(main_task, 'attachment', None))

    subject = main_task.subject or 'No Subject'
    if main_is_outgoing:
        primary_sender_name = main_task.sender_name or (main_task.assigned_user.username if main_task.assigned_user else 'ACVV Futura')
        primary_sender_email = main_task.sender_address or target_email
    else:
        primary_sender_name = main_task.sender_name or main_task.sender_address or 'Unknown Sender'
        primary_sender_email = main_task.sender_address or ''

    to_str = main_task.to_recipients or ''
    cc_str = main_task.cc_recipients or ''
    bcc_str = main_task.bcc_recipients or ''

    # Legacy fallback for older outgoing emails saved before to_recipients/cc_recipients existed
    if main_is_outgoing and not to_str:
        note_qs = ClientNotes.objects.filter(notes__icontains=subject)
        if main_task.mip_names:
            note_qs = note_qs.filter(
                Q(acvv_record__mip_names=main_task.mip_names) | Q(acvv_record__branch_code=main_task.mip_names)
            )
        matched_note = note_qs.order_by('-date').first()
        if matched_note and matched_note.notes:
            for line in matched_note.notes.splitlines():
                line_s = line.strip()
                if line_s.startswith("Recipient:"):
                    to_str = line_s.replace("Recipient:", "").strip()
                elif line_s.startswith("CC:") and not cc_str:
                    cc_str = line_s.replace("CC:", "").strip()
                elif line_s.startswith("BCC:") and not bcc_str:
                    bcc_str = line_s.replace("BCC:", "").strip()

    if not to_str:
        to_str = target_email if not main_is_outgoing else "Recipient"

    primary_date = main_task.received_at or main_task.delegated_at

    conversation_stream = [{
        'sender_name': primary_sender_name,
        'sender_email': primary_sender_email,
        'recipient': to_str,
        'cc': cc_str or '-',
        'bcc': bcc_str or '-',
        'subject': subject,
        'body': mark_safe(email_content),
        'date': primary_date,
        'type': 'OUTGOING' if main_is_outgoing else 'INCOMING',
        'attachments': attachments,
    }]

    timeline = []
    if is_reply_row:
        reply_to = clicked_task.to_recipients or "-"
        reply_cc = clicked_task.cc_recipients or "-"
        reply_bcc = clicked_task.bcc_recipients or "-"

        matched_tx = DelegationTransactionLog.objects.filter(
            action_type='EMAIL_REPLY',
            subject=clicked_task.subject
        ).order_by('-transaction_time').first()

        if reply_to == "-" and matched_tx and matched_tx.recipient_email:
            reply_to = matched_tx.recipient_email
        if reply_cc == "-" and matched_tx and matched_tx.cc_recipients:
            reply_cc = matched_tx.cc_recipients
        if reply_bcc == "-" and matched_tx and matched_tx.bcc_recipients:
            reply_bcc = matched_tx.bcc_recipients

        # Legacy note fallback if still missing
        if reply_to == "-":
            reply_note_qs = ClientNotes.objects.filter(notes__icontains=clicked_task.subject)
            if clicked_task.mip_names:
                reply_note_qs = reply_note_qs.filter(
                    Q(acvv_record__mip_names=clicked_task.mip_names) | Q(acvv_record__branch_code=clicked_task.mip_names)
                )
            reply_note = reply_note_qs.order_by('-date').first()
            if reply_note and reply_note.notes:
                for line in reply_note.notes.splitlines():
                    line_s = line.strip()
                    if line_s.startswith("Recipient:"):
                        reply_to = line_s.replace("Recipient:", "").strip() or "-"
                    elif line_s.startswith("CC:") and reply_cc == "-":
                        reply_cc = line_s.replace("CC:", "").strip() or "-"
                    elif line_s.startswith("BCC:") and reply_bcc == "-":
                        reply_bcc = line_s.replace("BCC:", "").strip() or "-"

        raw_reply_html = clicked_task.body or (matched_tx.body if matched_tx else "")
        clean_reply_html = strip_quoted_thread(raw_reply_html)
        reply_attachments = _get_local_attachments_for_email(clicked_task.email_id, getattr(clicked_task, 'attachment', None))

        reply_action_obj = {
            'action_type': 'EMAIL_REPLY',
            'recipient_email': reply_to,
            'subject': clicked_task.subject,
            'body': mark_safe(clean_reply_html),
            'user': clicked_task.assigned_user,
        }

        timeline.append({
            'type': 'action',
            'obj': reply_action_obj,
            'cc': reply_cc,
            'bcc': reply_bcc,
            'date': clicked_task.received_at or clicked_task.delegated_at or timezone.now(),
            'attachments': reply_attachments,
        })
    else:
        actions = DelegationTransactionLog.objects.filter(
            delegation=main_task
        ).exclude(action_type='EMAIL_REPLY').select_related('user').order_by('-transaction_time')

        for action in actions:
            timeline.append({
                'type': 'action',
                'obj': action,
                'cc': '-',
                'bcc': '-',
                'date': action.transaction_time,
                'attachments': [],
            })

    notes = DelegationNote.objects.filter(delegation=main_task).select_related('user').order_by('-created_at')
    for note in notes:
        timeline.append({
            'type': 'del_note',
            'obj': note,
            'date': getattr(note, 'created_at', timezone.now()),
            'attachments': [],
        })

    combined_timeline = sorted(timeline, key=lambda x: x['date'] if x['date'] else timezone.now(), reverse=True)

    context = {
        'task': main_task,
        'clicked_task': clicked_task,
        'email': {
            'subject': subject,
            'receivedDateTime': primary_date,
        },
        'email_body': mark_safe(email_content),
        'attachments': attachments,
        'conversation_stream': conversation_stream,
        'combined_timeline': combined_timeline,
        'notes': notes,
    }
    return render(request, 'acvv_app/outlook_view_thread.html', context)

@login_required
def export_temp_exists(request):
    """
    Generates and exports an Excel file by pulling data from the temp_exit table.
    """
    # Create a new workbook and select the active sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Temp Exists"

    # Define headers
    headers = [
        "MG Code", "Surname", "Initials", "MIP No.", "ID No.", 
        "Reason", "BIS From Date", "BIS End Date", 
        "Full Contributions Start Date", "Note"
    ]

    # Write headers and format them
    for col_num, header_title in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header_title
        cell.font = openpyxl.styles.Font(bold=True)

    # --- NEW: PULL DATA FROM DATABASE ---
    # Query all records from the manually created temp_exit table
    records = TempExit.objects.all().order_by('-created_at')

    # Write data rows
    for row_num, obj in enumerate(records, 2):
        ws.cell(row=row_num, column=1).value = obj.mg_code
        ws.cell(row=row_num, column=2).value = obj.surname
        ws.cell(row=row_num, column=3).value = obj.initials
        ws.cell(row=row_num, column=4).value = obj.mip_no
        ws.cell(row=row_num, column=5).value = obj.id_no
        ws.cell(row=row_num, column=6).value = obj.reason
        ws.cell(row=row_num, column=7).value = obj.bis_from_date
        ws.cell(row=row_num, column=8).value = obj.bis_end_date
        ws.cell(row=row_num, column=9).value = obj.full_contributions_start_date
        ws.cell(row=row_num, column=10).value = obj.note

    # Auto-adjust column widths for better readability
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[column].width = max_length + 2

    # Prepare the response
    filename = f"Temp_Exists_Export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response

@login_required
def reconciliation_worksheet(request):
    today = timezone.now().date()
    
    # 1. NAVIGATION LOGIC
    first_of_this_month = today.replace(day=1)
    last_month_date = (first_of_this_month - timedelta(days=1)).replace(day=1)

    req_year = request.GET.get('year')
    req_month = request.GET.get('month')
    
    if req_year and req_month:
        try:
            current_fiscal = datetime.strptime(f"{req_year}-{req_month}-01", '%Y-%m-%d').date()
        except ValueError:
            current_fiscal = first_of_this_month
    else:
        current_fiscal = first_of_this_month

    # 2. HANDLE POST ACTIONS (Save/Close/Reopen)
    if request.method == 'POST':
        if 'save_changes' in request.POST:
            row_ids = {key.split('_')[2] for key in request.POST.keys() if key.startswith('recon_status_')}
            for row_id in row_ids:
                row_obj = ReconciliationWorksheet.objects.filter(pk=row_id).first()
                if row_obj and not row_obj.is_closed:
                    row_obj.company_status = request.POST.get(f'company_status_{row_id}')
                    row_obj.payment_method = request.POST.get(f'payment_method_{row_id}')
                    row_obj.arrears = request.POST.get(f'arrears_{row_id}', '')
                    row_obj.member_count_reconciled = request.POST.get(f'member_count_{row_id}', 0) or 0
                    row_obj.contribution_amount_reconciled = request.POST.get(f'amount_{row_id}', 0.00) or 0.00
                    row_obj.lpi_amount = request.POST.get(f'lpi_amount_{row_id}', 0.00) or 0.00
                    row_obj.lpi_reason = request.POST.get(f'lpi_reason_{row_id}')
                    row_obj.debit_order_success = request.POST.get(f'debit_success_{row_id}')
                    row_obj.reconciled_status = request.POST.get(f'recon_status_{row_id}')
                    row_obj.date_schedule_received = request.POST.get(f'schedule_{row_id}') or None
                    row_obj.date_confirmed_on_step = request.POST.get(f'confirmed_{row_id}') or None
                    row_obj.debit_order_date = request.POST.get(f'debit_{row_id}') or None
                    row_obj.save()
            messages.success(request, "Progress saved successfully.")

        elif 'close_month' in request.POST:
            if not request.user.is_superuser:
                messages.error(request, "Permission Denied: Only Superusers can finalize a month.")
            else:
                records_to_close = ReconciliationWorksheet.objects.filter(fiscal_month=current_fiscal)
                for rec in records_to_close:
                    if rec.reconciled_status == 'Reconciled':
                        master_obj = Globalacvv.objects.filter(mip_names=rec.mg_name).first()
                        if master_obj and master_obj.notes:
                            try:
                                last_date = datetime.strptime(master_obj.notes, "%d.%m.%Y").date()
                                next_month_date = (last_date.replace(day=28) + timedelta(days=5)).replace(day=1)
                                new_note_val = next_month_date.strftime("%d.%m.%Y")
                            except:
                                new_note_val = current_fiscal.strftime("01.%m.%Y")
                        else:
                            new_note_val = current_fiscal.strftime("01.%m.%Y")
                        
                        Globalacvv.objects.filter(mip_names=rec.mg_name).update(
                            notes=new_note_val,
                            member=str(rec.member_count_reconciled),
                            contribution_amount=str(rec.contribution_amount_reconciled)
                        )

                records_to_close.update(is_closed=True, closed_at=timezone.now())
                messages.success(request, f"Fiscal month {current_fiscal.strftime('%B %Y')} closed. Master list updated.")
            return redirect(f"{reverse('reconciliation_worksheet')}?year={current_fiscal.year}&month={current_fiscal.month}")

        elif 'reopen_month' in request.POST:
            if not request.user.is_superuser:
                messages.error(request, "Permission Denied: Only Superusers can re-open a month.")
            else:
                ReconciliationWorksheet.objects.filter(fiscal_month=current_fiscal).update(is_closed=False, closed_at=None)
                messages.warning(request, f"Fiscal month {current_fiscal.strftime('%B %Y')} RE-OPENED.")
            return redirect(f"{reverse('reconciliation_worksheet')}?year={current_fiscal.year}&month={current_fiscal.month}")

    # 3. FETCH & AUTO-GENERATE DATA (Updated: Runs every time to catch newly added master records)
    for item in Globalacvv.objects.all():
        clean_code = str(item.branch_code).strip().upper()
        ReconciliationWorksheet.objects.get_or_create(
            fiscal_month=current_fiscal,
            mg_code=clean_code, 
            defaults={'mg_name': item.mip_names}
        )

    records = ReconciliationWorksheet.objects.filter(
        Q(fiscal_month=current_fiscal) | 
        Q(fiscal_month__lt=current_fiscal, reconciled_status='Unreconciled', is_closed=False)
    ).order_by('mg_code', 'fiscal_month')

    # 4. ANNOTATIONS
    last_ws_recon_sub = ReconciliationWorksheet.objects.filter(
        mg_name=OuterRef('mg_name'),
        mg_code=OuterRef('mg_code'),
        fiscal_month__lt=current_fiscal,
        reconciled_status='Reconciled'
    ).order_by('-fiscal_month').values('fiscal_month')[:1]

    records = records.annotate(
        acvv_member_count=Subquery(Globalacvv.objects.filter(mip_names=OuterRef('mg_name')).values('member')[:1]),
        master_start_date=Subquery(Globalacvv.objects.filter(mip_names=OuterRef('mg_name')).values('notes')[:1]),
        last_reconciled_ws=Subquery(last_ws_recon_sub)
    )

    total_members = 0
    total_contribution = 0.00

    for r in records:
        last_date = None
        
        if r.last_fiscal_reconciled and r.last_fiscal_reconciled.strip():
            r.last_fiscal_display = r.last_fiscal_reconciled
            try:
                last_date = datetime.strptime(r.last_fiscal_reconciled, "%B %Y").date()
            except:
                last_date = None
        elif r.last_reconciled_ws:
            last_date = r.last_reconciled_ws
            r.last_fiscal_display = last_date.strftime("%B %Y")
        elif r.master_start_date:
            try:
                last_date = datetime.strptime(str(r.master_start_date).strip(), "%d.%m.%Y").date()
                r.last_fiscal_display = last_date.strftime("%B %Y")
            except:
                last_date = None
                r.last_fiscal_display = r.master_start_date
        else:
            r.last_fiscal_display = "No Data"

        if last_date:
            diff = (current_fiscal.year - last_date.year) * 12 + (current_fiscal.month - last_date.month)
            r.is_overdue = diff >= 2
        else:
            r.is_overdue = True

        # Sum current fiscal month values for the summary cards
        if r.fiscal_month == current_fiscal:
            try:
                m_count = int(r.member_count_reconciled) if r.member_count_reconciled is not None else int(r.acvv_member_count or 0)
            except (ValueError, TypeError):
                m_count = 0
            
            try:
                c_amount = float(r.contribution_amount_reconciled) if r.contribution_amount_reconciled is not None else 0.00
            except (ValueError, TypeError):
                c_amount = 0.00
                
            total_members += m_count
            total_contribution += c_amount

    return render(request, 'acvv_app/reconciliation_worksheet.html', {
        'records': records,
        'display_name': current_fiscal.strftime("%B %Y"),
        'history': ReconciliationWorksheet.objects.values('fiscal_month').distinct().order_by('-fiscal_month'),
        'is_closed': ReconciliationWorksheet.objects.filter(fiscal_month=current_fiscal, is_closed=True).exists(),
        'current_fiscal': current_fiscal,
        'total_members': total_members,
        'total_contribution': total_contribution,
    })

@login_required
def export_reconciliation_worksheet(request, date_str):
    try:
        fiscal_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse("Invalid date format", status=400)

    last_ws_recon_sub = ReconciliationWorksheet.objects.filter(
        mg_name=OuterRef('mg_name'),
        fiscal_month__lt=fiscal_date,
        reconciled_status='Reconciled'
    ).order_by('-fiscal_month').values('fiscal_month')[:1]

    acvv_member_sub = Globalacvv.objects.filter(mip_names=OuterRef('mg_name')).values('member')[:1]
    acvv_notes_sub = Globalacvv.objects.filter(mip_names=OuterRef('mg_name')).values('notes')[:1]
    acvv_email_sub = Globalacvv.objects.filter(mip_names=OuterRef('mg_name')).values('mg_email_address')[:1]

    records = ReconciliationWorksheet.objects.filter(fiscal_month=fiscal_date).annotate(
        acvv_member_count=Subquery(acvv_member_sub),
        master_start_date=Subquery(acvv_notes_sub),
        last_reconciled_ws=Subquery(last_ws_recon_sub),
        acvv_email_address=Subquery(acvv_email_sub)
    )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Recon {fiscal_date.strftime('%b %Y')}"

    headers = [
        "MG Name", "MG Code", "Email Address", "Company Status", "Payment Method", 
        "Last Fiscal Reconciled", "Arrears", "Member Count Reconciled", 
        "Contribution Amount Reconciled", "LPI Amount", "LPI Reason", "Reconciled Status", 
        "Date Schedule Received", "Date Confirmed on Step", "Debit order date"
    ]
    ws.append(headers)

    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True)

    for r in records:
        display_status = r.company_status if r.company_status else "Active"
        if display_status.lower() in ['done', 'active']:
            display_status = "Active"

        if r.last_reconciled_ws:
            display_recon = r.last_reconciled_ws.strftime("%B %Y")
        elif r.master_start_date:
            try:
                d = datetime.strptime(r.master_start_date, "%d.%m.%Y").date()
                display_recon = d.strftime("%B %Y")
            except:
                display_recon = r.master_start_date
        else:
            display_recon = "No Data"

        ws.append([
            r.mg_name, r.mg_code, r.acvv_email_address, display_status, r.payment_method,
            display_recon, r.arrears,
            r.member_count_reconciled or r.acvv_member_count,
            r.contribution_amount_reconciled, 
            r.lpi_amount, 
            r.lpi_reason, 
            r.reconciled_status,
            r.date_schedule_received, r.date_confirmed_on_step, r.debit_order_date
        ])

    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except: pass
        ws.column_dimensions[column].width = max_length + 2

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f'attachment; filename="Reconciliation_Worksheet_{date_str}.xlsx"'
    wb.save(response)
    return response

@login_required
def export_reconciliation(request, date_str):
    try:
        fiscal_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse("Invalid date format", status=400)

    records = ReconciliationRecord.objects.filter(fiscal_month=fiscal_date)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Summary {fiscal_date.strftime('%b %Y')}"
    headers = ["Member Group", "Branch Code", "Billed", "Paid", "Outstanding", "Note"]
    ws.append(headers)
    
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True)

    for r in records:
        ws.append([r.mip_name, r.branch_code, r.billed_amount, r.paid_amount, r.outstanding_amount, r.note])
        
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f'attachment; filename="Reconciliation_Summary_{date_str}.xlsx"'
    wb.save(response)
    return response

@login_required
def outlook_email_list(request):
    """
    View to display NEW, DELEGATED (DEL), and COMPLETED (COM) emails with date filtering.
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # --- FIX: Expanded statuses inclusion list filter matrix targets ---
    emails = EmailDelegation.objects.filter(
        status__in=['NEW', 'DEL', 'COM']
    ).select_related('assigned_user').order_by('-received_at')

    # Apply date filters if provided
    if start_date and end_date:
        emails = emails.filter(received_at__date__range=[start_date, end_date])

    # Status counts for badges (Calculated post base filter execution alignment)
    new_count = EmailDelegation.objects.filter(status='NEW').count()
    del_count = EmailDelegation.objects.filter(status='DEL').count()
    # --- ADDED: Track and expose Completed status metrics safely ---
    com_count = EmailDelegation.objects.filter(status='COM').count()

    context = {
        'emails': emails,
        'new_count': new_count,
        'del_count': del_count,
        'com_count': com_count,  # 👈 Available for badge counters inside your HTML layout view template
    }
    return render(request, 'acvv_app/outlook_email_list.html', context)

@login_required
def export_email_tasks_excel(request):
    """
    Exports the filtered email task list to Excel.
    Includes NEW, DEL, and COM (Completed) records.
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # 🔑 FIX: Added 'COM' to include completed tasks inside your spreadsheet export query matrix
    emails = EmailDelegation.objects.filter(status__in=['NEW', 'DEL', 'COM']).order_by('-received_at')
    
    if start_date and end_date:
        emails = emails.filter(received_at__date__range=[start_date, end_date])

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Email Task Export"

    # Styles
    header_fill = PatternFill(start_color="43A047", end_color="43A047", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    headers = ['Status', 'Received Date', 'Subject', 'Sender', 'Member Group', 'Assigned To', 'Category']
    ws.append(headers)

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal='center')

    for e in emails:
        ws.append([
            e.get_status_display(),
            e.received_at.strftime('%Y-%m-%d %H:%M') if e.received_at else '',
            e.subject,
            e.sender_address,
            e.mip_names,
            e.assigned_user.username if e.assigned_user else 'Unassigned',
            e.email_category
        ])

    # Column Widths
    widths = [15, 20, 40, 30, 20, 20, 20]
    for i, width in enumerate(widths):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i+1)].width = width

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="Email_Tasks_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    wb.save(response)
    return response

@login_required
def temp_exists_list(request):
    # Handle New Entry or Update Submission
    if request.method == 'POST':
        exit_id = request.POST.get('exit_id')
        
        data_fields = {
            'mg_code': request.POST.get('mg_code'),
            'surname': request.POST.get('surname'),
            'initials': request.POST.get('initials'),
            'mip_no': request.POST.get('mip_no'),
            'id_no': request.POST.get('id_no'),
            'reason': request.POST.get('reason'),
            'bis_from_date': request.POST.get('bis_from') or None,
            'bis_end_date': request.POST.get('bis_end') or None,
            'full_contributions_start_date': request.POST.get('full_start') or None,
            'note': request.POST.get('note')
        }

        if exit_id:
            # Update existing record
            exit_record = get_object_or_404(TempExit, pk=exit_id)
            for field, value in data_fields.items():
                setattr(exit_record, field, value)
            exit_record.save()
            messages.success(request, "Temp Exit updated successfully.")
        else:
            # Create new record
            TempExit.objects.create(**data_fields)
            messages.success(request, "Temp Exit added successfully.")
            
        return redirect('temp_exists_list')

    # Display existing entries
    exits = TempExit.objects.all().order_by('-created_at')
    return render(request, 'acvv_app/temp_exists.html', {'exits': exits})

@login_required
def download_acvv_email(request, delegation_id):
    """
    Streams the saved .eml file directly from local disk via FileResponse.
    Falls back to a one-time 8 KB disk download from Graph for legacy incoming emails,
    or synthesizes a clean Outlook-compatible RFC822 .eml from local DB + local attachments.
    """
    from django.utils.text import slugify

    try:
        if str(delegation_id).isdigit():
            task = get_object_or_404(EmailDelegation, pk=delegation_id)
        else:
            task = get_object_or_404(EmailDelegation, email_id=delegation_id)
    except Exception:
        messages.error(request, "Task record not found.")
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

    ms_id = str(task.email_id or '')
    target_email = getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'lorraine@futurasa.co.za')
    eml_filename = f"{slugify(task.subject or 'email')[:50] or 'record'}.eml"

    # 1. Serve directly from local disk if already archived
    if task.eml_file_path:
        abs_eml = os.path.join(settings.MEDIA_ROOT, task.eml_file_path)
        if os.path.exists(abs_eml) and os.path.getsize(abs_eml) > 0:
            return FileResponse(
                open(abs_eml, 'rb'),
                as_attachment=True,
                filename=eml_filename,
                content_type='message/rfc822'
            )

    is_outgoing = (
        task.status == 'SENT'
        or ms_id.startswith(('SENT-', 'LOCAL-', 'REPLY-', 'CLAIM-', 'DIRECT_'))
    )

    # 2. For legacy incoming emails not yet archived on disk, attempt a one-time 8 KB disk stream from Graph
    if not is_outgoing and ms_id:
        eml_rel = download_raw_eml_to_disk(ms_id, target_email=target_email)
        if eml_rel:
            task.eml_file_path = eml_rel
            task.save(update_fields=['eml_file_path'])
            abs_eml = os.path.join(settings.MEDIA_ROOT, eml_rel)
            if os.path.exists(abs_eml):
                return FileResponse(
                    open(abs_eml, 'rb'),
                    as_attachment=True,
                    filename=eml_filename,
                    content_type='message/rfc822'
                )

    # 3. Synthesize a clean Outlook-compatible .eml from local DB + all local attachments
    att_tuples = []
    local_atts = AcvvEmailAttachment.objects.filter(email_id=ms_id, is_inline=False).order_by('id')
    for att in local_atts:
        abs_p = os.path.join(settings.MEDIA_ROOT, att.file_path)
        if os.path.exists(abs_p):
            att_tuples.append((att.name, abs_p, att.content_type))

    if not att_tuples and getattr(task, 'attachment', None):
        try:
            legacy_p = task.attachment.path
            if os.path.exists(legacy_p):
                att_tuples.append((os.path.basename(legacy_p), legacy_p, None))
        except Exception:
            pass

    eml_bytes = build_clean_eml_bytes(
        subject=task.subject or 'No Subject',
        sender=task.sender_address or target_email,
        recipient=task.to_recipients or (target_email if not is_outgoing else 'Recipient'),
        html_body=task.body or 'Body content not found in local record.',
        cc=task.cc_recipients,
        bcc=task.bcc_recipients,
        sent_dt=task.received_at or task.delegated_at or timezone.now(),
        attachment_paths=att_tuples,
    )

    safe_filename = urllib.parse.quote(eml_filename)
    response = HttpResponse(eml_bytes, content_type='message/rfc822')
    response['Content-Disposition'] = f"attachment; filename=\"{safe_filename}\"; filename*=UTF-8''{safe_filename}"
    return response

def get_branch_map_acvv(claims_queryset):
    """Helper to map company codes to formal Branch names for ACVV."""
    codes = claims_queryset.values_list('company_code', flat=True).distinct()
    branches = Globalacvv.objects.filter(mip_names__in=codes)
    return {b.mip_names: b.member for b in branches}


@login_required
def export_two_pot_invoice_cecile(request):
    """
    Report 1: Cecile Invoice Format (Grey Theme)
    Filters records where the status is valid, qualified is 'YES',
    and a submission date exists.
    """
    from io import BytesIO

    query = request.GET.get('q')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Initial Query
    claims = AcvvClaim.objects.filter(claim_type='Two Pot').order_by('claim_created_date')
    if query:
        claims = claims.filter(Q(id_number__icontains=query) | Q(member_surname__icontains=query))
    if start_date and end_date:
        claims = claims.filter(claim_created_date__range=[start_date, end_date])

    wb = openpyxl.Workbook()
    ws = wb.active
    if ws is None:
        ws = wb.create_sheet(title="Cecile Invoice")
    else:
        ws.title = "Cecile Invoice"

    header_fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin'),
    )

    headers = [
        "Date", "Initials", "Surname", "Member nr", "ID NUMBER", "Fund",
        "Branch", "Admin From", "Qualified", "Date submitted online",
        "Successful Loaded confirmation", "Admin Fee R33 + 15% Vat", "SUBMIT ONLINE"
    ]
    ws.append(headers)

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = Font(bold=True, size=10)
        cell.border = thin_border
        cell.alignment = Alignment(horizontal='center')

    branch_map = get_branch_map_acvv(claims)

    valid_statuses = [
        "PAID",
        "MEMBER EMERGENCY SAVINGS POT WITHDRAWAL SUBMITTED",
        "MEMBER EMERGENCY SAVINGS POT WITHDRAWAL REQUESTED",
    ]

    for claim in claims:
        current_status = str(claim.claim_status or "").upper().strip()
        is_valid_status = current_status in valid_statuses
        is_qualified = (claim.qualified == "YES")

        if not (is_valid_status and is_qualified):
            continue

        if not claim.date_submitted:
            continue

        initials = "".join([n[0] for n in claim.member_name.split() if n]) if claim.member_name else ""

        ws.append([
            claim.claim_created_date.strftime('%d/%m/%Y') if claim.claim_created_date else '',
            initials,
            claim.member_surname,
            claim.mip_number,
            claim.id_number,
            claim.company_code,
            branch_map.get(claim.company_code, ""),
            claim.agent or "",
            "yes",
            claim.date_submitted.strftime('%d/%m/%Y'),
            "YES",
            "R37.95",
            "SUBMIT ONLINE",
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="Cecile_Invoice_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    return response

@login_required
def export_two_pot_tracking_acvv(request):
    """
    Report 2: Full Tracking (Yellow Theme) with Red text for 'NO' statuses.
    Matches attached image format.
    Extracts Tracking Parameters from claim notes.
    """
    query = request.GET.get('q')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # --- UPDATED: Added prefetch_related('notes') for efficient querying ---
    claims_queryset = AcvvClaim.objects.filter(claim_type='Two Pot').prefetch_related('notes').order_by('claim_created_date')

    if query:
        claims_queryset = claims_queryset.filter(
            Q(id_number__icontains=query) | Q(member_surname__icontains=query) | 
            Q(company_code__icontains=query) | Q(mip_number__icontains=query)
        )

    if start_date and end_date:
        claims_queryset = claims_queryset.filter(claim_created_date__range=[start_date, end_date])

    # Fetch unique company codes to minimize database hits
    unique_codes = claims_queryset.values_list('company_code', flat=True).distinct()
    
    # Map the branch_code (fund code) to the mip_names (company name)
    company_name_map = {
        item['branch_code']: item['mip_names'] 
        for item in Globalacvv.objects.filter(branch_code__in=unique_codes).values('branch_code', 'mip_names')
    }

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Two-Pot Tracking"

    yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    
    now = timezone.now()
    display_start = start_date if start_date else now.replace(day=1).strftime('%d.%m.%Y')
    display_end = end_date if end_date else now.strftime('%d.%m.%Y')
    
    # Row 1 Title (Billing Period)
    ws.merge_cells('A1:O1')
    header_cell = ws['A1']
    header_cell.value = f"Billing - Member Emergency Savings Pot Withdrawal Requested - {display_start} to {display_end}"
    header_cell.font = Font(bold=True, size=11, underline="single")
    header_cell.fill = yellow_fill
    header_cell.border = thin_border

    # Row 2 Headers
    headers = [
        "Date application extracted from Web: Savings Form Request",  # Column B
        "Initials",                                                   # Column C
        "Surname",                                                    # Column D
        "Member number",                                              # Column E
        "ID NUMBER",                                                  # Column F
        "Fund Code",                                                  # Column G
        "Company Name",                                               # Column H
        "Query",                                                      # Column I
        "Claim",                                                      # Column J
        "Qualified Y/N",                                              # Column K
        "Date submitted online",                                      # Column L
        "Inform Employer that the claim is succesfully loaded",       # Column M
        "Admin Front Office Application Submitted",                   # Column N
        "Note"                                                        # Column O
    ]
    ws.append(headers)
    
    for cell in ws[2]:
        cell.font = Font(bold=True, size=9)
        cell.fill = yellow_fill
        cell.border = thin_border
        cell.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
    ws.row_dimensions[2].height = 45

    for claim in claims_queryset:
        initials = "".join([n[0] for n in claim.member_name.split() if n]) if claim.member_name else ""
        
        # --- NEW: Default variables for extraction ---
        # We start with fallbacks based on original claim data, then overwrite if a note is found
        is_paid = str(claim.claim_status).upper().strip() == "PAID"
        qualified_val = "YES" if is_paid else "NO"
        informed_er = "YES" if is_paid else "NO"
        date_submitted_online = claim.date_submitted.strftime('%d/%m/%Y') if claim.date_submitted else ''
        submitted_by_agent = claim.agent or "TD"

        # --- NEW: Extract Tracking Parameters via Regex ---
        for note in claim.notes.all():
            if note.note_description and "[Tracking Parameters Logged]" in note.note_description:
                desc = note.note_description
                
                # Extract 'Qualified'
                q_match = re.search(r"- Qualified:\s*([^\n]+)", desc)
                if q_match:
                    qualified_val = q_match.group(1).strip().upper()
                    
                # Extract 'Informed ER'
                er_match = re.search(r"- Informed ER:\s*([^\n]+)", desc)
                if er_match:
                    informed_er = er_match.group(1).strip().upper()

                # Extract 'Date Submitted Online'
                date_match = re.search(r"- Date Submitted Online:\s*([^\n]+)", desc)
                if date_match and date_match.group(1).strip() != 'N/A':
                    date_submitted_online = date_match.group(1).strip()

                # Extract 'Submitted by Agent'
                agent_match = re.search(r"- Submitted by Agent:\s*([^\n]+)", desc)
                if agent_match and agent_match.group(1).strip() != 'N/A':
                    submitted_by_agent = agent_match.group(1).strip()
        # ------------------------------------------------

        # Build out dynamic Note helper descriptions for Column O when NO is encountered
        note_helper = ""
        if qualified_val == "NO":
            status_str = str(claim.claim_status).strip()
            if "Already claim" in status_str:
                note_helper = "Member already claimed this financial year"
            else:
                note_helper = ""

        company_name = company_name_map.get(claim.company_code, "Unknown Company")

        row = [
            claim.claim_created_date.strftime('%d/%m/%Y') if claim.claim_created_date else '', # Col B
            initials,                                                                          # Col C
            claim.member_surname,                                                              # Col D
            claim.mip_number,                                                                  # Col E
            claim.id_number,                                                                   # Col F
            claim.company_code,                                                                # Col G
            company_name,                                                                      # Col H 
            "Savings Form Request",                                                            # Col I 
            claim.claim_status or "",                                                          # Col J
            qualified_val,                                                                     # Col K (Extracted)
            date_submitted_online,                                                             # Col L (Extracted)
            informed_er,                                                                       # Col M (Extracted)
            submitted_by_agent,                                                                # Col N (Extracted)
            note_helper                                                                        # Col O
        ]
        ws.append(row)

        # Apply Red Text formatting targets to lines evaluating as "NO" 
        for cell in ws[ws.max_row]:
            cell.border = thin_border
            cell.alignment = Alignment(vertical='center', horizontal='left')
            if qualified_val == "NO":
                cell.font = Font(size=9, color="FF0000")
            else:
                cell.font = Font(size=9)

    widths = [30, 8, 18, 14, 18, 12, 35, 22, 35, 12, 22, 22, 22, 50]
    for i, width in enumerate(widths):
        ws.column_dimensions[get_column_letter(i+1)].width = width

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="Two_Pot_Full_Tracking_{now.strftime("%Y_%m_%d")}.xlsx"'
    wb.save(response)
    return response

@login_required
def send_acvv_direct_email(request, company_code):
    """
    Handles the 'Compose New Email' form.
    Correctly splits multiple recipients, sends via Graph, and archives all
    attachments + an Outlook-compatible .eml file locally.
    """
    if request.method == 'POST':
        recipient_raw = request.POST.get('member_recipient_email', '')
        cc_raw = (request.POST.get('member_cc_email') or request.POST.get('email_cc') or '').strip()
        bcc_raw = (request.POST.get('member_bcc_email') or request.POST.get('email_bcc') or '').strip()
        subject = request.POST.get('member_email_subject_reply')
        body = request.POST.get('email_body_html_content')
        selected_action_type = request.POST.get('action_note_type') or request.POST.get('action_log_type') or "Correspondence"
        attachments = request.FILES.getlist('email_attachments')

        if recipient_raw and subject and body:
            target_email = settings.OUTLOOK_EMAIL_ADDRESS
            recipient_list = [email.strip() for email in re.split('[;,]', recipient_raw) if email.strip()]
            clean_recipient_str = ", ".join(recipient_list)

            current_username = request.user.username.lower()
            current_firstname = request.user.first_name.lower() if request.user.first_name else ""

            agent_name = request.user.get_full_name() or request.user.username.replace('_', ' ').title()
            agent_title = "Administrator"

            if 'timothy' in current_username or 'timothy' in current_firstname:
                agent_name = "Timothy Davids"
                agent_title = "Indexing Specialist"
            elif 'jesica' in current_username or 'jessica' in current_username or 'jesica' in current_firstname:
                agent_name = "Jesica Haynes"
                agent_title = "Reconciliations Specialist"
            elif 'luanovaneck' in current_username or 'luano' in current_firstname:
                agent_name = "Luano van Eck"
                agent_title = "Developer"
            elif 'omega' in current_username:
                agent_name = "Omega System Assistant"
                agent_title = "Automated System"

            signature_context = {
                'request': request,
                'agent_name': agent_name,
                'agent_title': agent_title,
                'logo_url': 'https://acvv.futurasa.co.za/static/images/futura_logo.png'
            }
            signature_html = render_to_string('acvv_app/acvv_email_signature.html', signature_context)
            full_html_body = f"<div>{body}</div><br><br>{signature_html}"

            result = OutlookGraphService.send_outlook_email(
                target_email,
                recipient_list,
                subject,
                full_html_body,
                content_type='Html',
                attachments=attachments,
                cc=cc_raw,
                bcc=bcc_raw,
                user=None
            )

            if result.get('success'):
                sent_now = timezone.now()
                acvv_record = get_object_or_404(Globalacvv, Q(mip_names=company_code) | Q(branch_code=company_code))
                new_ms_id = f"SENT-{int(sent_now.timestamp())}-{request.user.id}"

                eml_rel_path, saved_atts = save_outgoing_email_locally(
                    owner_key=new_ms_id,
                    subject=subject,
                    sender=target_email,
                    recipient=clean_recipient_str,
                    html_body=full_html_body,
                    cc=cc_raw,
                    bcc=bcc_raw,
                    uploaded_files=attachments,
                    sent_dt=sent_now,
                )

                EmailDelegation.objects.create(
                    email_id=new_ms_id,
                    subject=(subject or '(No Subject)')[:255],
                    body=full_html_body,
                    sender_address=target_email,
                    sender_name=agent_name,
                    to_recipients=clean_recipient_str,
                    cc_recipients=cc_raw,
                    bcc_recipients=bcc_raw,
                    assigned_user=request.user,
                    status='SENT',
                    mip_names=acvv_record.mip_names,
                    received_at=sent_now,
                    delegated_at=sent_now,
                    work_related=True,
                    communication_type='Email',
                    has_attachments=bool(saved_atts),
                    eml_file_path=eml_rel_path,
                    is_fully_synced=True,
                )

                cc_seg = f"\nCC: {cc_raw}" if cc_raw else ""
                bcc_seg = f"\nBCC: {bcc_raw}" if bcc_raw else ""
                ClientNotes.objects.create(
                    acvv_record=acvv_record,
                    notes=f"Email Sent: {subject}\nRecipient: {clean_recipient_str}{cc_seg}{bcc_seg}",
                    user=request.user.username,
                    date=sent_now,
                    communication_type="Email",
                    action_note_type=selected_action_type
                )

                messages.success(request, f"Email sent and archived locally for {clean_recipient_str}.")
            else:
                messages.error(request, f"Email failed: {result.get('error')}")
        else:
            messages.warning(request, "Please fill in all required fields.")

    return redirect('acvv_information', mip_names=company_code)

@login_required
def protected_media_serve(request, path):
    """
    Serves files under MEDIA_ROOT only to authenticated users via FileResponse.
    Falls back strictly to legacy upload subfolders in BASE_DIR so existing live
    member documents keep working until the server admin moves them into media/.
    """
    normalized_path = os.path.normpath(path).replace('\\', '/').lstrip('/')
    abs_media_root = os.path.abspath(settings.MEDIA_ROOT)
    abs_file_path = os.path.abspath(os.path.join(abs_media_root, normalized_path))

    # 1. Check new dedicated MEDIA_ROOT (ACVV_APP/media/) first
    if abs_file_path.startswith(abs_media_root) and os.path.isfile(abs_file_path):
        content_type = mimetypes.guess_type(abs_file_path)[0] or 'application/octet-stream'
        return FileResponse(open(abs_file_path, 'rb'), content_type=content_type)

    # 2. Safe legacy fallback ONLY for the 5 known upload directories in BASE_DIR
    allowed_legacy_prefixes = (
        'branch_docs/',
        'claim_attachments/',
        'email_attachments/',
        'notes/',
        'notes_attachments/',
    )
    if normalized_path.startswith(allowed_legacy_prefixes):
        abs_base_dir = os.path.abspath(settings.BASE_DIR)
        legacy_file_path = os.path.abspath(os.path.join(abs_base_dir, normalized_path))
        if legacy_file_path.startswith(abs_base_dir) and os.path.isfile(legacy_file_path):
            content_type = mimetypes.guess_type(legacy_file_path)[0] or 'application/octet-stream'
            return FileResponse(open(legacy_file_path, 'rb'), content_type=content_type)

    raise Http404("Media file not found.")

@login_required
def serve_local_attachment_view(request, att_pk):
    """
    Streams a locally stored attachment or inline CID image directly from disk
    via FileResponse behind @login_required (zero RAM bloat).
    Automatically appends '.eml' to attached emails (message/rfc822) that have
    no file extension so Outlook opens them with a single click.
    """
    att = get_object_or_404(AcvvEmailAttachment, pk=att_pk)
    abs_path = os.path.join(settings.MEDIA_ROOT, att.file_path)
    if not os.path.exists(abs_path):
        raise Http404("Local attachment file not found on disk.")

    download_name = (att.name or os.path.basename(abs_path)).strip()
    content_type = att.content_type or mimetypes.guess_type(download_name)[0] or 'application/octet-stream'

    # Detect attached emails (message/rfc822 or extensionless RFC822 files) and ensure .eml extension
    is_email_attachment = content_type.lower() == 'message/rfc822'
    if not is_email_attachment and '.' not in os.path.basename(download_name):
        try:
            with open(abs_path, 'rb') as peek_f:
                head = peek_f.read(512).decode('latin-1', errors='ignore')
            if any(h in head for h in ('From:', 'Received:', 'MIME-Version:', 'Subject:')) and '\n' in head:
                is_email_attachment = True
                content_type = 'message/rfc822'
        except Exception:
            pass

    if is_email_attachment and not download_name.lower().endswith('.eml'):
        download_name = f"{download_name}.eml"

    response = FileResponse(open(abs_path, 'rb'), content_type=content_type)
    if not att.is_inline:
        safe_ascii = download_name.replace('"', "'")
        safe_utf8 = urllib.parse.quote(download_name)
        response['Content-Disposition'] = f"attachment; filename=\"{safe_ascii}\"; filename*=UTF-8''{safe_utf8}"
    return response


@login_required
def download_outlook_attachment(request, delegation_id, attachment_id):
    """
    Serves attachments from local disk first via FileResponse.
    Falls back to 8 KB chunked streaming from Outlook Graph API /$value only if not yet on disk.
    """
    delegation = get_object_or_404(EmailDelegation, pk=delegation_id)
    target_email = getattr(settings, 'OUTLOOK_EMAIL_ADDRESS', 'lorraine@futurasa.co.za')

    # 1. Check local disk first
    local_att = AcvvEmailAttachment.objects.filter(
        email_id=delegation.email_id
    ).filter(
        Q(attachment_id=str(attachment_id)) | Q(id=int(attachment_id) if str(attachment_id).isdigit() else -1)
    ).first()

    if local_att:
        abs_path = os.path.join(settings.MEDIA_ROOT, local_att.file_path)
        if os.path.exists(abs_path):
            content_type = local_att.content_type or mimetypes.guess_type(local_att.name)[0] or 'application/octet-stream'
            return FileResponse(
                open(abs_path, 'rb'),
                as_attachment=True,
                filename=local_att.name,
                content_type=content_type
            )

    # 2. Fallback: stream raw binary chunks from Graph /$value
    meta_endpoint = f"messages/{delegation.email_id}/attachments/{attachment_id}?$select=name,contentType"
    meta_data = OutlookGraphService._make_graph_request(meta_endpoint, target_email)

    if not isinstance(meta_data, dict) or 'error' in meta_data:
        messages.error(request, "Could not fetch attachment metadata from Outlook.")
        return redirect(request.META.get('HTTP_REFERER', 'outlook_delegated_box'))

    file_name = meta_data.get('name', 'attachment')
    content_type = meta_data.get('contentType', 'application/octet-stream')

    file_stream = OutlookGraphService.stream_attachment_mime(target_email, delegation.email_id, attachment_id)
    if not file_stream:
        messages.error(request, "Could not open attachment stream from Outlook.")
        return redirect(request.META.get('HTTP_REFERER', 'outlook_delegated_box'))

    safe_filename = urllib.parse.quote(file_name)
    response = StreamingHttpResponse(file_stream, content_type=content_type)
    response['Content-Disposition'] = f"attachment; filename=\"{safe_filename}\"; filename*=UTF-8''{safe_filename}"
    return response

@login_required
def acvv_sla_report_view(request):
    # Rights Check
    if not request.user.is_superuser:
        messages.error(request, "Access Denied: Superuser rights required for SLA Reports.")
        return redirect('dashboard')

    start_str = request.GET.get('start_date')
    end_str = request.GET.get('end_date')
    
    def get_valid_date(date_val):
        if date_val and date_val != "None" and date_val != "":
            return parse_date(date_val)
        return None

    # 1. Setup Filters
    recon_q = Q()
    email_q = Q() # Added for Emails
    start_dt = get_valid_date(start_str)
    end_dt = get_valid_date(end_str)

    if start_dt:
        recon_q &= Q(updated_at__date__gte=start_dt)
        email_q &= Q(delegated_at__date__gte=start_dt) # Added for Emails
    if end_dt:
        recon_q &= Q(updated_at__date__lte=end_dt)
        email_q &= Q(delegated_at__date__lte=end_dt) # Added for Emails

    # 2. Handle Excel Export
    if request.GET.get('export') == 'excel':
        # Updated to pass both Q objects
        return export_acvv_sla_excel(recon_q, email_q)

    # 3. Aggregate Totals (Reconciliations)
    status_breakdown = ReconciliationWorksheet.objects.filter(recon_q).values(
        'reconciled_status'
    ).annotate(total=Count('id'))

    user_breakdown = ReconciliationWorksheet.objects.filter(recon_q).values(
        'updated_by__username'
    ).annotate(total=Count('id')).order_by('-total')

    # 4. Aggregate Totals (Email Delegations) - UPDATED FOR MULTI-TYPE LOGS
    # Grouping by both status and communication_type to capture 'Claim Sent', 'Two Pot Email', 'Reply'
    email_status_breakdown = EmailDelegation.objects.filter(email_q).values(
        'status', 'communication_type'
    ).annotate(total=Count('id'))

    email_user_breakdown = EmailDelegation.objects.filter(email_q).values(
        'assigned_user__username'
    ).annotate(total=Count('id')).order_by('-total')

    # Calculate Totals
    total_recon = sum(item['total'] for item in status_breakdown)
    total_emails = sum(item['total'] for item in email_status_breakdown)

    context = {
        'status_breakdown': status_breakdown,
        'user_breakdown': user_breakdown,
        'email_status_breakdown': email_status_breakdown, # Added
        'email_user_breakdown': email_user_breakdown,     # Added
        'total_actions': total_recon + total_emails,     # Grand Total
        'total_recon': total_recon,
        'total_emails': total_emails,
        'start_date': start_str,
        'end_date': end_str,
    }
    
    return render(request, 'acvv_app/acvv_sla_report.html', context)

def export_acvv_sla_excel(recon_q, email_q):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    
    wb = openpyxl.Workbook()
    
    # --- Styles ---
    header_font = Font(bold=True, color="FFFFFF")
    recon_fill = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
    email_fill = PatternFill(start_color="1565C0", end_color="1565C0", fill_type="solid")
    center_align = Alignment(horizontal="center")

    # ==========================================
    # SHEET 1: RECONCILIATIONS (Original)
    # ==========================================
    ws1 = wb.active
    ws1.title = "ACVV Reconciliation Audit"
    headers1 = ['MG Code', 'MG Name', 'Fiscal Month', 'Status', 'Agent', 'Last Updated', 'Contribution Amount']
    ws1.append(headers1)
    
    for cell in ws1[1]:
        cell.font, cell.fill, cell.alignment = header_font, recon_fill, center_align

    queryset_recon = ReconciliationWorksheet.objects.filter(recon_q).select_related('updated_by').order_by('-updated_at')
    for r in queryset_recon:
        ws1.append([
            r.mg_code, r.mg_name,
            r.fiscal_month.strftime('%B %Y') if r.fiscal_month else '',
            r.reconciled_status,
            r.updated_by.username if r.updated_by else "System",
            r.updated_at.strftime('%Y-%m-%d %H:%M') if r.updated_at else '',
            r.contribution_amount_reconciled
        ])

    # ==========================================
    # SHEET 2: EMAIL DELEGATIONS (Updated Columns)
    # ==========================================
    ws2 = wb.create_sheet(title="Email Audit Trail")
    # --- FIX: Appended 'Log Type' column into headers matrix layout array ---
    headers2 = ['Subject', 'Sender', 'Assigned To', 'Status', 'Log Type', 'Category', 'Delegated At']
    ws2.append(headers2)

    for cell in ws2[1]:
        cell.font, cell.fill, cell.alignment = header_font, email_fill, center_align

    queryset_email = EmailDelegation.objects.filter(email_q).select_related('assigned_user').order_by('-delegated_at')
    for e in queryset_email:
        # --- FIX: Ensure incoming 'communication_type' outputs cleanly alongside fallback values ---
        resolved_log_type = e.communication_type or "Email"

        ws2.append([
            e.subject,
            e.sender_address,
            e.assigned_user.username if e.assigned_user else "Unassigned",
            e.get_status_display(),
            resolved_log_type, # ➔ Displays 'Claim Sent', 'Two Pot Email', 'Reply', etc.
            e.email_category,
            e.delegated_at.strftime('%Y-%m-%d %H:%M') if e.delegated_at else ''
        ])

    # Auto-adjust column widths for both sheets
    for sheet in [ws1, ws2]:
        for col in sheet.columns:
            sheet.column_dimensions[col[0].column_letter].width = 25

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="ACVV_Full_SLA_Report_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    wb.save(response)
    return response

@login_required
def import_acvv_csv(request):
    if request.method == "POST":
        file = request.FILES.get('csv_upload')
        
        if not file:
            messages.error(request, "Please select a file.")
            return redirect('import_acvv_csv')

        try:
            # 1. Define columns to force as strings to prevent .0 decimals
            string_cols = {
                'ACCOUNT NUMBER': str, 
                'MG Code': str, 
                'NPO CODE': str,
                'MG Contact Tel. 1': str,
                'MG Contact Tel. 2': str
            }

            # 2. Check file extension and load with dtype
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, dtype=string_cols)
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file, dtype=string_cols)
            else:
                messages.error(request, "Unsupported file format. Please upload CSV or Excel.")
                return redirect('import_acvv_csv')

            # 3. Clean up any remaining .0 from pandas auto-conversion
            # This turns '53361366398.0' into '53361366398'
            for col in string_cols.keys():
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True)
                    # Replace 'nan' string (from empty cells) with empty string
                    df[col] = df[col].replace('nan', '')

            # Fill remaining NaN values with None for DB compatibility
            df = df.where(pd.notnull(df), None)
            
            records_created = 0
            records_updated = 0

            for _, row in df.iterrows():
                mip_name_val = row.get('Member Group Name')
                if not mip_name_val:
                    continue

                defaults_data = {
                    'branch_code': row.get('MG Code', ''),
                    'status': row.get('Company Status', ''),
                    'member': row.get('Member Count', ''),
                    'contribution_amount': row.get('Bill Amount', ''),
                    'mg_email_address': row.get('MG Contact Email', ''),
                    'tel': row.get('MG Contact Tel. 1', ''),
                    'tel_2': row.get('MG Contact Tel. 2', ''),
                    'npo_code': row.get('NPO CODE', ''),
                    'mg_bank_info': row.get('MG BANK INFO', ''),
                    'bank': row.get('BANK', ''),
                    'branch': row.get('BRANCH', ''),
                    'account_number': row.get('ACCOUNT NUMBER', ''),
                    'account_name': row.get('ACCOUNT NAME', ''),
                    'account_type': row.get('ACCOUNT TYPE', ''),
                    'employer_contacts': row.get('EMPLOYER CONTACTS', ''),
                    'schedule_date_received': row.get('Last Recon - Date', '')
                }

                obj, created = Globalacvv.objects.update_or_create(
                    mip_names=str(mip_name_val),
                    defaults=defaults_data
                )
                
                if created: records_created += 1
                else: records_updated += 1

            messages.success(request, f"Import complete! Created: {records_created}, Updated: {records_updated}.")
            
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            
        return redirect('import_acvv_csv')

    return render(request, 'acvv_app/import_acvv.html')

from django.db import connection, transaction

@login_required
def import_reconciliation_csv(request):
    if request.method == "POST":
        file = request.FILES.get('csv_upload')
        if not file:
            messages.error(request, "Please select a file.")
            return redirect('import_reconciliation_csv')

        try:
            # 1. Load file
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file, engine='openpyxl')

            # 2. Helpers
            def clean_decimal(val):
                if pd.isna(val) or val == '' or val is None: 
                    return 0.00
                
                # Convert to string and clean out currency symbols, commas, and hidden spaces
                val_str = str(val).upper()
                for char in ['R', '$', 'ZAR', ',', ' ', '\xa0']:
                    val_str = val_str.replace(char, '')
                
                try:
                    return float(val_str)
                except ValueError:
                    return 0.00

            def clean_date_to_str(val):
                if pd.isna(val) or val == '' or val is None:
                    return None
                dt = pd.to_datetime(val, errors='coerce')
                if pd.notna(dt):
                    return dt.strftime('%Y-%m-%d')
                return None

            records_updated = 0
            
            with transaction.atomic():
                with connection.cursor() as cursor:
                    
                    # df.values converts data to list of rows, bypassing headers entirely
                    for row in df.values:
                        
                        # =========================================================
                        # EXACT MAPPING BASED ON YOUR EXCEL COLUMNS
                        # =========================================================
                        col_company_name    = 0  # MG Name
                        col_company_code    = 1  # MG Code
                        # col 2 is Email Address (Skipped)
                        col_company_status  = 3  # Company Status
                        col_payment_method  = 4  # Payment Method
                        col_fiscal_month    = 5  # Last Fiscal Reconciled
                        # col 6 is Arrears (Skipped)
                        col_members         = 7  # Member Count Reconciled
                        col_amount          = 8  # Contribution Amount Reconciled
                        col_current_status  = 9  # Reconciled Status
                        col_date_schedule   = 10 # Date Schedule Received
                        col_date_step       = 11 # Date Confirmed on Step
                        col_date_debit      = 12 # Debit order date
                        # =========================================================

                        # 1. Extract Identifiers First
                        company_code = str(row[col_company_code]).strip() if pd.notna(row[col_company_code]) else ''
                        fiscal_month = clean_date_to_str(row[col_fiscal_month])
                        
                        # Skip if essential identifiers are missing
                        if not company_code or company_code.lower() == 'nan' or not fiscal_month:
                            continue

                        # 2. Clean Dates
                        d1 = clean_date_to_str(row[col_date_schedule])
                        d2 = clean_date_to_str(row[col_date_step])
                        d3 = clean_date_to_str(row[col_date_debit])

                        # 3. Safely Extract Members (Handling missing or text data)
                        members_count = row[col_members]
                        if pd.isna(members_count) or members_count == '':
                            members_count = 0
                        else:
                            try:
                                members_count = int(float(members_count))
                            except ValueError:
                                members_count = 0

                        # 4. Safely Extract Amount
                        contribution_amount = clean_decimal(row[col_amount])
                        
                        # 5. Extract Basic Strings Safely
                        company_name = str(row[col_company_name]).strip() if pd.notna(row[col_company_name]) else ''
                        company_status = str(row[col_company_status]).strip() if pd.notna(row[col_company_status]) else 'Active'
                        payment_method = str(row[col_payment_method]).strip() if pd.notna(row[col_payment_method]) else 'Debit Order'
                        reconciled_status = str(row[col_current_status]).strip() if pd.notna(row[col_current_status]) else 'Unreconciled'

                        # 6. Database Insertion/Update
                        sql = """
                            INSERT INTO reconciliation_worksheet 
                            (mg_code, fiscal_month, mg_name, company_status, payment_method, 
                             member_count_reconciled, contribution_amount_reconciled, reconciled_status, 
                             date_schedule_received, date_confirmed_on_step, debit_order_date)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                            mg_name=VALUES(mg_name), company_status=VALUES(company_status), 
                            payment_method=VALUES(payment_method), member_count_reconciled=VALUES(member_count_reconciled),
                            contribution_amount_reconciled=VALUES(contribution_amount_reconciled),
                            reconciled_status=VALUES(reconciled_status),
                            date_schedule_received=VALUES(date_schedule_received),
                            date_confirmed_on_step=VALUES(date_confirmed_on_step),
                            debit_order_date=VALUES(debit_order_date)
                        """
                        
                        params = (
                            company_code, fiscal_month, company_name, company_status, payment_method,
                            members_count, contribution_amount, reconciled_status,
                            d1, d2, d3
                        )
                        
                        cursor.execute(sql, params)
                        records_updated += 1

            messages.success(request, f"Successfully processed {records_updated} records.")
        except Exception as e:
            messages.error(request, f"Import failed: {str(e)}")
            
        return redirect('import_reconciliation_csv')
    
    return render(request, 'acvv_app/import_reconciliation.html')

import re

@login_required
def import_withdrawals(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        file = request.FILES['excel_file']
        
        # Helper to clean date strings that might contain extra text
        def clean_and_parse_date(val):
            if not val: return None
            val_str = str(val).strip()
            # Regex finds DD.MM.YYYY format
            match = re.search(r'\d{2}\.\d{2}\.\d{4}', val_str)
            if match:
                return pd.to_datetime(match.group(0), dayfirst=True).date()
            return None

        try:
            df = pd.read_excel(file)
            df.columns = df.columns.str.strip()
            df = df.where(pd.notnull(df), None)

            for index, row in df.iterrows():
                # Primary Key Lookup
                id_no = str(row.get('ID_Passport', '')).strip()
                if not id_no: continue
                
                # Strict Mapping based on your provided table
                defaults = {
                    'company_code': row.get('FUDN CODE', 'UNKNOWN'),
                    'mip_number': row.get('Member Nr', ''),
                    'member_name': row.get('Member Name', ''),
                    'member_surname': row.get('Member Surname', ''),
                    'claim_created_date': clean_and_parse_date(row.get('Claim Created')),
                    'claim_type': row.get('Claim Type', 'Two Pot'),
                    'exit_reason': row.get('Exit Reason', ''),
                    'claim_allocation': row.get('Claim Allocation', 'New Claim'),
                    'claim_status': row.get('Claim Status', 'Submitted'),
                    'date_paid': clean_and_parse_date(row.get('DATE CLAIM PAID')),
                    'last_contribution_date': clean_and_parse_date(row.get('J_Last_Contribution - EXIT DATE')),
                    'date_submitted': clean_and_parse_date(row.get('Date Submitted')),
                    'vested_pot_paid_date': clean_and_parse_date(row.get('Vested Pot Date Paid')),
                    'savings_pot_paid_date': clean_and_parse_date(row.get('Savigns Pot Date Paid')),
                    'infund_cert_date': clean_and_parse_date(row.get('Paid Up Certificate')),
                    'payment_option': row.get('Pay Full Benefit / Retirement', ''),
                    
                    # Calculated Booleans
                    'vested_pot_available': bool(row.get('Vested Pot Date Paid')),
                    'savings_pot_available': bool(row.get('Savigns Pot Date Paid')),
                }

                # Update existing or create new
                claim_obj, created = AcvvClaim.objects.update_or_create(
                    id_number=id_no,
                    defaults=defaults
                )

                # Add Note from the 'NOTES' Excel Column
                note_content = row.get('NOTES')
                if note_content:
                    ClaimNote.objects.create(
                        claim=claim_obj,
                        note_selection="IMPORT",
                        note_description=f"Excel Import Note: {note_content}",
                        created_by=request.user
                    )

            messages.success(request, "Withdrawals imported successfully.")
        except Exception as e:
            print(f"IMPORT ERROR: {e}") 
            messages.error(request, f"Import Failed: {str(e)}")
            
        return redirect('global_two_pot')
    
    return render(request, 'acvv_app/import_withdrawals.html')

@login_required
def import_two_pot_claims(request):
    if request.method == "POST":
        file = request.FILES.get('claim_upload')
        if not file:
            messages.error(request, "Please select a file to upload.")
            return redirect('import_two_pot_claims')

        try:
            # 1. Load file safely (CSV or XLSX)
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file, engine='openpyxl')

            # 2. Clean headers to prevent mismatch errors (removes trailing/leading spaces)
            df.columns = df.columns.str.strip()

            # 3. Date cleaning helper function
            def clean_date_to_obj(val):
                if pd.isna(val) or val == '' or val is None:
                    return None
                dt = pd.to_datetime(val, errors='coerce')
                if pd.notna(dt):
                    return dt.date()
                return None

            records_created = 0
            records_updated = 0
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    
                    # --- Extract Core Identifiers ---
                    # Using .get() prevents the script from crashing if a column is entirely missing
                    id_number = str(row.get('ID NUMBER', '')).strip()
                    
                    if not id_number or id_number.lower() == 'nan':
                        continue # Skip empty rows

                    # --- Extract Dates ---
                    claim_created_date = clean_date_to_obj(row.get('Date application extracted from Web: Savings Form Request'))
                    date_submitted = clean_date_to_obj(row.get('Date submitted online'))

                    # --- Extract Strings Safely ---
                    company_code = str(row.get('Company Name', '')).strip()
                    agent = str(row.get('agent', '')).strip()
                    member_name = str(row.get('Initials', '')).strip()
                    member_surname = str(row.get('Surname', '')).strip()
                    mip_number = str(row.get('Member number', '')).strip()
                    claim_type = str(row.get('claim_type', 'Two Pot')).strip() # Default to Two Pot if empty
                    claim_status = str(row.get('Claim', 'New Claim')).strip()
                    payment_option = str(row.get('Payment Option', '')).strip()
                    claim_allocation = str(row.get('Claim Allocation', '')).strip()

                    # Handle pandas NaN turning into the string "nan"
                    if company_code.lower() == 'nan': company_code = ''
                    if agent.lower() == 'nan': agent = ''
                    if member_name.lower() == 'nan': member_name = ''
                    if member_surname.lower() == 'nan': member_surname = ''
                    if mip_number.lower() == 'nan': mip_number = ''
                    if payment_option.lower() == 'nan': payment_option = ''
                    if claim_allocation.lower() == 'nan': claim_allocation = ''

                    # --- Database Insert / Update ---
                    # update_or_create checks if a claim for this ID Number and Type already exists.
                    # If it does, it updates it. If not, it creates a new one.
                    claim, created = AcvvClaim.objects.update_or_create(
                        id_number=id_number,
                        claim_type=claim_type,
                        defaults={
                            'company_code': company_code,
                            'agent': agent,
                            'member_name': member_name,
                            'member_surname': member_surname,
                            'mip_number': mip_number,
                            'claim_status': claim_status,
                            'payment_option': payment_option,
                            'claim_created_date': claim_created_date,
                            'date_submitted': date_submitted,
                            'claim_allocation': claim_allocation,
                        }
                    )
                    
                    if created:
                        records_created += 1
                    else:
                        records_updated += 1

            messages.success(request, f"Import complete! Created {records_created} new claims and updated {records_updated} existing claims.")
        
        except Exception as e:
            messages.error(request, f"Import failed due to a system error: {str(e)}")
            
        return redirect('import_two_pot_claims') # Adjust this to your actual redirect URL name
    
    # GET request - render the upload page
    return render(request, 'acvv_app/two_pot_import.html')
