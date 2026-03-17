import base64
from itertools import count
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from django.db.models import Q
from django.urls import reverse # Required for clean redirects
from django.conf import settings # Required for target_email default

from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.core.files.storage import FileSystemStorage

# Core Django Auth Models
from django.contrib.auth.models import User
import openpyxl
import requests 

# Local Model Imports
from .models import AcvvClaim, BranchDocument, ClaimNote, Globalacvv, ClientNotes, EmailDelegation, DelegationNote, DelegationTransactionLog, ReconciliationRecord, ReconciliationWorksheet, TempExit


# Import the new Graph API service functions
from .services.outlook_graph_service import fetch_inbox_messages, send_outlook_email, _make_graph_request

# Import Delegation Service functions
from .services.delegation_service import (
    get_or_create_delegation_status, 
    delegate_email_task, 
    add_delegation_note, 
    get_delegated_emails_for_user,
    log_delegation_transaction
)

from dateutil import parser

from django.utils.safestring import mark_safe # for the email body & signature

from django.http import HttpResponse

from django.db.models import OuterRef, Subquery, Q

# --------------------------------------------------------------------- #
# AUTHENTICATION VIEWS (REMAINS THE SAME)
# --------------------------------------------------------------------- #

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

@login_required
def dashboard(request):
    username = request.user.username
    is_outlook_admin = request.user.username.lower() == 'omega' or request.user.is_superuser
    
    # NEW COUNT LOGIC
    # Undelegated: Status is NEW and it is marked as work related
    undelegated_count = EmailDelegation.objects.filter(status='NEW', work_related=True).count()
    
    # Recycle Bin: Filter specifically for the new 'DLT' status
    recycled_count = EmailDelegation.objects.filter(status='DLT').count()
    
    # My Tasks: Status is 'DEL' (Delegated) for the logged-in user
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
    """
    Logs the user out.
    """
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')

def index(request):
    """
    Handles the root URL, redirecting to the login page.
    """
    return redirect('login') 

# --------------------------------------------------------------------- #
# OUTLOOK DELEGATOR VIEWS (Inbox & Assignment)
# --------------------------------------------------------------------- #

@login_required
def outlook_dashboard_view(request):
    """
    Displays the Live Inbox. Only shows emails that are WORK RELATED and NOT YET DELEGATED.
    """
    if request.user.username.lower() != 'omega' and not request.user.is_superuser:
        messages.error(request, "Access restricted.")
        return redirect('outlook_delegated_box')

    target_email = request.GET.get('email', settings.OUTLOOK_EMAIL_ADDRESS)
    context = {'target_email': target_email, 'messages': []}
    
    inbox_data = fetch_inbox_messages(target_email, 10000) 
    
    if 'error' not in inbox_data:
        emails = inbox_data.get('value', [])
        email_ids = [email['id'] for email in emails]
        
        processed_ids = EmailDelegation.objects.filter(
            email_id__in=email_ids
        ).exclude(status='NEW', work_related=True).values_list('email_id', flat=True)

        display_emails = []
        
        for email in emails:
            email_id = email['id']
            if email_id in processed_ids:
                continue

            received_date_str = email.get('receivedDateTime') 
            # --- NEW: Extract Sender Address ---
            sender_email = email.get('from', {}).get('emailAddress', {}).get('address', '')
            
            # Update/Create record with sender info
            delegation, created = EmailDelegation.objects.get_or_create(
                email_id=email_id,
                defaults={
                    'received_at': parser.isoparse(received_date_str) if received_date_str else None,
                    'status': 'NEW',
                    'work_related': True,
                    'sender_address': sender_email, # Save sender
                    'subject': email.get('subject', '(No Subject)')
                }
            )
            
            # If the record already existed but sender was missing, update it
            if not created and not delegation.sender_address:
                delegation.sender_address = sender_email
                delegation.save()

            try:
                if received_date_str:
                    email['receivedDateTime'] = parser.isoparse(received_date_str)
            except Exception: pass

            email['delegation_status'] = delegation.get_status_display()
            email['assigned_user'] = delegation.assigned_user.username if delegation.assigned_user else None
            email['delegation_id'] = delegation.pk 
            display_emails.append(email)

        context['messages'] = display_emails
    else:
        context['error'] = f"Error: {inbox_data['error']}"

    return render(request, 'acvv_app/outlook_dashboard.html', context)


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
        
        # Call the service function, passing the target_email as the sender mailbox
        result = send_outlook_email(target_email, recipient, subject, body)
        
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


# --------------------------------------------------------------------- #
# OUTLOOK DELEGATED VIEWS (Assigned User Workflow)
# --------------------------------------------------------------------- #

@login_required
def outlook_delegated_box(request):
    """
    Dashboard view: Fetch delegations assigned to the user that are NOT completed.
    Assumes 'DEL' is Delegated/Active.
    """
    # Fetch delegations assigned to the user with status 'DEL'
    # We exclude 'COM' (Completed) so they are removed from the dashboard
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
    Allows the assigned user to view the full email, add notes, 
    update metadata, reply (with attachments), and mark as completed.
    """
    delegation = get_object_or_404(EmailDelegation, pk=delegation_id)
    
    if delegation.assigned_user != request.user:
        messages.error(request, "You are not assigned to this task.")
        return redirect('outlook_delegated_box')

    target_email = settings.OUTLOOK_EMAIL_ADDRESS 

    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        # 1. Handle Task Completion
        if action_type == 'complete_task':
            delegation.status = 'COM'
            delegation.save()
            log_delegation_transaction(delegation_id, request.user, "TASK COMPLETED", "Email marked as completed.", action_type='TASK_COMPLETE')
            messages.success(request, f"Task #{delegation_id} archived.")
            return redirect('outlook_delegated_box')

        # 2. Handle Metadata Update
        elif action_type == 'update_metadata':
            delegation.mip_names = request.POST.get('mip_names')
            delegation.email_category = request.POST.get('email_category')
            delegation.communication_type = request.POST.get('communication_type')
            delegation.save()
            log_delegation_transaction(delegation_id, request.user, f"Metadata Updated", "System", action_type='METADATA_UPDATE')
            messages.success(request, "Task metadata updated.")
            return redirect('outlook_delegated_action', delegation_id=delegation_id)

        # 3. Handle Note Submission
        elif action_type == 'add_note':
            note_content = request.POST.get('note_content')
            success, message = add_delegation_note(delegation_id, request.user, note_content)
            if success: messages.success(request, message)
            return redirect('outlook_delegated_action', delegation_id=delegation_id)
        
        # 4. Handle Reply
        elif action_type == 'send_reply':
            recipient = request.POST.get('reply_recipient')
            subject = request.POST.get('reply_subject')
            body = request.POST.get('reply_body')
            attachment = request.FILES.get('email_attachment')
            
            result = send_outlook_email(target_email, recipient, subject, body, content_type='Html', attachment=attachment)
            
            if result.get('success'):
                log_delegation_transaction(delegation_id, request.user, subject, recipient, action_type='EMAIL_REPLY')
                messages.success(request, "Reply sent.")
            else:
                messages.error(request, f"Reply failed: {result.get('error')}")
            return redirect('outlook_delegated_action', delegation_id=delegation_id)

    # --- FETCH Data for GET ---
    acvv_records = Globalacvv.objects.all().only('mip_names', 'branch_code')
    
    # FETCH 1: Message Content
    email_data = _make_graph_request(f"messages/{delegation.email_id}", target_email)
    
    # 🛑 FETCH 2: Attachments (Added for Preview) 🛑
    attachment_endpoint = f"messages/{delegation.email_id}/attachments"
    attachment_data = _make_graph_request(attachment_endpoint, target_email)
    attachments = attachment_data.get('value', []) if 'error' not in attachment_data else []

    if 'error' in email_data:
        messages.error(request, f"Error fetching content: {email_data.get('error')}")
        return redirect('outlook_delegated_box')

    context = {
        'delegation': delegation,
        'email': email_data,
        'attachments': attachments, # 👈 Passed to template
        'notes': delegation.notes.all().order_by('-created_at'),
        'acvv_records': acvv_records,
        'target_email': target_email,
    }
    return render(request, 'acvv_app/outlook_delegated_action.html', context)


# --------------------------------------------------------------------- #
# ACVV App Views (Existing)
# --------------------------------------------------------------------- #
@login_required
def export_acvv_list_excel(request):
    """Exports filtered ACVV records to Excel with specific column mapping."""
    search_query = request.GET.get('search_query')
    records = Globalacvv.objects.all()

    if search_query:
        records = records.filter(
            Q(mip_names__icontains=search_query) |
            Q(branch_code__icontains=search_query)
        )
    
    records = records.order_by('mip_names')

    # Create Workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ACVV Records Export"

    # Specific Headers requested
    headers = [
        'Member Group Name', 'MG Code', 'Company Status', 
        'Last Recon - Status', 'Member Count', 'Last Recon - Date', 
        'Bill Amount', 'MG Contact Email', 'MG Contact Tel. 1', 'MG Contact Tel. 2'
    ]
    ws.append(headers)

    # Style Header
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="43a047", end_color="43a047", fill_type="solid")
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill

    # Map database records to the Excel columns
    for record in records:
        ws.append([
            record.mip_names,                      # Member Group Name
            record.branch_code or "-",             # MG Code
            record.status or "-",                  # Company Status
            "",                                    # Last Recon - Status (Blank per request)
            record.member or "-",                  # Member Count
            "",                                    # Last Recon - Date (Blank per request)
            record.contribution_amount or "-",     # Bill Amount
            record.mg_email_address or "-",        # MG Contact Email
            record.tel or "-",                     # MG Contact Tel. 1
            ""                                     # MG Contact Tel. 2 (Blank per request)
        ])

    # Auto-adjust column width
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
    """
    acvv_records = Globalacvv.objects.all()
    search_query = request.GET.get('search_query')

    # Apply search filter
    if search_query:
        acvv_records = acvv_records.filter(
            Q(mip_names__icontains=search_query) |
            Q(branch_code__icontains=search_query)
        )

    # Order the results
    acvv_records = acvv_records.order_by('mip_names')

    context = {
        'acvv_records': acvv_records,
        'search_query': search_query or ''
    }
    return render(request, 'acvv_app/acvv_list.html', context)

from django.db.models import Q # For flexible filtering

@login_required
def acvv_information(request, mip_names):
    """
    Detailed view for a specific ACVV record with unified logging.
    FIXED: No longer pulls redundant 'Email Sent' notes from ClientNotes.
    """
    acvv_record = get_object_or_404(Globalacvv, mip_names=mip_names)
    
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
                    acvv_record=acvv_record, notes=note_content,
                    user=request.user.username, date=timezone.now(),
                    communication_type=comm_type, action_note_type=action_note,
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
                    branch_name=acvv_record.mip_names, file_name=pdf_file.name,
                    file_path=file_url, uploaded_by=request.user.username
                )
                messages.success(request, "PDF added.")
                return redirect(f'/acvv-records/{acvv_record.mip_names}/#pdf-upload')

    # --- DATA FETCHING ---
    # We filter notes to EXCLUDE anything that was tagged as an email, 
    # so they don't show up in the notes tab as duplicates.
    notes = ClientNotes.objects.filter(acvv_record=acvv_record).exclude(
        Q(notes__icontains="Email Composed") | Q(notes__icontains="Email Sent")
    ).order_by('-date')
    
    company_claims = AcvvClaim.objects.filter(company_code=mip_names).order_by('-claim_created_date')
    branch_docs = BranchDocument.objects.filter(branch_name=mip_names).order_by('-uploaded_at')

    # --- EMAIL LOG LOGIC (Unified) ---
    # We pull ONLY from EmailDelegation. This is the source of truth for the Email Log.
    delegated_logs = EmailDelegation.objects.filter(
        Q(mip_names__icontains=acvv_record.mip_names) | Q(mip_names__icontains=acvv_record.branch_code)
    ).select_related('assigned_user')

    combined_email_log = []

    for log in delegated_logs:
        is_sent = (log.status == 'SENT')
        combined_email_log.append({
            'type': 'DIRECT' if is_sent else 'ORIGINAL',
            'icon': '📤' if is_sent else '📩',
            'badge_color': '#28a745' if is_sent else ('#1976d2' if log.status != 'DLT' else '#ef5350'), 
            'subject': log.subject or "Outlook Task",
            'received_at': log.received_at,
            'assigned_to': log.assigned_user.username if log.assigned_user else "Unassigned",
            'display_type': 'SENT' if is_sent else log.get_status_display(),
            'email_id': log.email_id,
            # If your EmailDelegation model doesn't have an attachment field, 
            # we'll need to add it there to make the "Download" work perfectly.
            'file_url': log.attachment.url if hasattr(log, 'attachment') and log.attachment else None,
            'sort_date': log.received_at or log.delegated_at
        })

    # Sort the unified log by date
    combined_email_log.sort(key=lambda x: x['sort_date'] if x['sort_date'] else datetime.min, reverse=True)

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
    available_users = User.objects.filter(is_active=True).exclude(pk=request.user.pk)
    acvv_records = Globalacvv.objects.all().values('mip_names', 'branch_code')
    
    # 1. Fetch the main Email Message
    endpoint = f"messages/{email_id}" 
    email_data = _make_graph_request(endpoint, target_email) 

    if 'error' in email_data:
        messages.error(request, "Could not fetch email content.")
        return redirect('outlook_dashboard')

    # 2. Fetch Attachments (Includes contentBytes for the preview)
    attachment_endpoint = f"messages/{email_id}/attachments"
    attachment_data = _make_graph_request(attachment_endpoint, target_email)
    attachments = attachment_data.get('value', []) if 'error' not in attachment_data else []

    email_subject = email_data.get('subject', '(No Subject)')
    sender_email = email_data.get('from', {}).get('emailAddress', {}).get('address', '')

    if request.method == 'POST':
        work_related_raw = request.POST.get('work_related')
        is_work_related = (work_related_raw == 'Yes')
        assignee_pk = request.POST.get('agent_name')
        mip_names_value = request.POST.get('mip_names')
        
        data_for_delegation = {
            'mip_names': mip_names_value,
            'subject': email_subject,
            'sender_address': sender_email,
            'email_category': request.POST.get('email_category'),
            'work_related': is_work_related, 
            'status': 'DEL' if is_work_related else 'DLT',
            'comm_type': request.POST.get('email_method', 'Email'),
        }
        
        if not is_work_related:
            delegation = get_or_create_delegation_status(email_id)
            delegation.work_related = False 
            delegation.status = 'DLT'
            delegation.subject = email_subject
            delegation.sender_address = sender_email
            delegation.mip_names = mip_names_value
            delegation.save()
            
            messages.success(request, "Task moved to Recycle Bin.")
            return redirect('outlook_dashboard')
        else:
            if assignee_pk and assignee_pk not in ['', '__Select Agent__']:
                success, message = delegate_email_task(
                    email_id, 
                    assignee_pk, 
                    request.user, 
                    classification_data=data_for_delegation
                )
                
                if success:
                    EmailDelegation.objects.filter(email_id=email_id).update(
                        work_related=True, 
                        status='DEL',
                        subject=email_subject,
                        sender_address=sender_email
                    )
                    messages.success(request, f"Task delegated to {mip_names_value}!")
                    return redirect('outlook_dashboard')
                else:
                    messages.error(request, message)
            else:
                messages.error(request, "Please select an agent.")

    context = {
        'email_id': email_id,
        'email_subject': email_subject,
        'email_sender': sender_email,
        'email_content': email_data.get('body', {}).get('content', ''), 
        'attachments': attachments,
        'available_users': available_users,
        'acvv_records': acvv_records,
    }
    return render(request, 'acvv_app/outlook_delegate_to.html', context)

def outlook_email_content(request, email_id):
    """
    Fetches the raw HTML content of an email and returns it as a response 
    to be loaded by an iframe's 'src' attribute.
    """
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    endpoint = f"messages/{email_id}" 
    email_data = _make_graph_request(endpoint, target_email)

    if 'error' in email_data:
        return HttpResponse("<h1>Error fetching email content.</h1>", status=500)

    body_data = email_data.get('body', {})
    
    if body_data.get('contentType', '').lower() == 'html':
        content = body_data.get('content', 'No HTML body found.')
    else:
        # If plain text, wrap in <pre> tags
        content = body_data.get('content', 'No email body found.')
        content = f'<pre style="white-space: pre-wrap; word-wrap: break-word; font-family: sans-serif;">{content}</pre>'

    # Wrap in a full HTML document (essential for iframe rendering)
    wrapped_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>body {{ font-family: sans-serif; margin: 15px; }}</style>
    </head>
    <body>
        {content}
    </body>
    </html>
    """
    
    # Return as plain HTML response (not marked safe, but the browser loads it securely)
    return HttpResponse(wrapped_content, content_type='text/html')


from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth

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

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.dateparse import parse_date
from django.conf import settings
from .models import AcvvClaim, Globalacvv, EmailDelegation
from .services.outlook_graph_service import _make_graph_request # Assuming your service name

@login_required
def global_claims_view(request):
    """Register for ALL claims EXCEPT Two Pot."""
    query = request.GET.get('q')
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    
    base_claims = AcvvClaim.objects.exclude(claim_type='Two Pot')

    if query:
        claims = base_claims.filter(
            Q(id_number__icontains=query) | 
            Q(member_surname__icontains=query) | 
            Q(company_code__icontains=query)
        ).order_by('-claim_created_date')
    else:
        claims = base_claims.order_by('-claim_created_date')[:50] 

    # --- UPDATED: Email Preview Logic ---
    # Fetch IDs as strings to handle both legacy (int) and new (string) formats
    delegation_ids = [str(c.linked_email_id) for c in claims if c.linked_email_id]
    
    if delegation_ids:
        # Fetching bulk using string keys
        delegations_map = EmailDelegation.objects.in_bulk(delegation_ids, field_name='email_id')
        
        for claim in claims:
            if claim.linked_email_id:
                # 🛑 REMOVED int() conversion to allow long string IDs
                del_obj = delegations_map.get(str(claim.linked_email_id))
                if del_obj:
                    endpoint = f"messages/{del_obj.email_id}?$select=subject,from,body,receivedDateTime"
                    email_data = _make_graph_request(endpoint, target_email)
                    if 'error' not in email_data:
                        claim.email_preview_subject = email_data.get('subject')
                        claim.email_preview_sender = email_data.get('from', {}).get('emailAddress', {}).get('address')
                        claim.email_preview_body = email_data.get('body', {}).get('content')
                        claim.email_preview_date = email_data.get('receivedDateTime')

    return render(request, 'acvv_app/global_claims.html', {
        'claims': claims,
        'all_companies': Globalacvv.objects.values('mip_names', 'branch_code'),
        # Ensure we can see 'DEL' (Incoming) and 'SENT' (Replies) to link them
        'my_delegated_emails': EmailDelegation.objects.filter(assigned_user=request.user).exclude(status='DLT'),
        'is_two_pot_view': False 
    })

@login_required
def global_two_pot_view(request):
    """Dedicated Register for ONLY Two Pot claims with Note/Attachment support."""
    query = request.GET.get('q')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    target_email = settings.OUTLOOK_EMAIL_ADDRESS

    # --- HARD FILTER: Only Two Pot ---
    # Added prefetch_related('notes') to load history and attachments efficiently
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
    paginator = Paginator(base_claims, 15) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Email Preview Logic
    delegation_pks = [c.linked_email_id for c in page_obj if c.linked_email_id]
    if delegation_pks:
        # Filter out invalid IDs that aren't numeric to avoid the ValueError we saw earlier
        numeric_pks = [pk for pk in delegation_pks if str(pk).isdigit()]
        delegations_map = EmailDelegation.objects.in_bulk(numeric_pks)
        
        for claim in page_obj:
            if claim.linked_email_id and str(claim.linked_email_id).isdigit():
                try:
                    del_obj = delegations_map.get(int(claim.linked_email_id))
                    if del_obj:
                        email_data = _make_graph_request(
                            f"messages/{del_obj.email_id}?$select=subject,from,body,receivedDateTime", 
                            target_email
                        )
                        if 'error' not in email_data:
                            claim.email_preview_subject = email_data.get('subject')
                            claim.email_preview_sender = email_data.get('from', {}).get('emailAddress', {}).get('address')
                            claim.email_preview_body = email_data.get('body', {}).get('content')
                            claim.email_preview_date = email_data.get('receivedDateTime')
                except Exception as e:
                    print(f"DEBUG: Email Preview Error for Claim {claim.id}: {e}")
                    continue

    # Rendering the SPECIFIC Two Pot HTML (Ensure the template path matches your project)
    return render(request, 'acvv_app/two_pot_global.html', {
        'page_obj': page_obj, 
        'claims': page_obj, # This ensures the notes-templates loop works
        'all_companies': Globalacvv.objects.values('mip_names', 'branch_code'),
        'my_delegated_emails': EmailDelegation.objects.filter(assigned_user=request.user, status='DEL').order_by('-received_at'),
        'is_two_pot_view': True,
        'search_query': query,
        'start_date': start_date,
        'end_date': end_date,
    })

@login_required
def save_global_claim(request):
    """Unified save view with note handling, file attachments, and email with attachments."""
    if request.method == 'POST':
        claim_id = request.POST.get('claim_id')
        claim_type = request.POST.get('claim_type') 
        company_code = request.POST.get('company_code')
        
        linked_id = request.POST.get('linked_email_id') or None

        data = {
            'company_code': company_code,
            'agent': request.POST.get('agent'),
            'id_number': request.POST.get('id_number'),
            'member_name': request.POST.get('member_name'),
            'member_surname': request.POST.get('member_surname'),
            'mip_number': request.POST.get('mip_number'),
            'claim_type': claim_type,
            'claim_status': request.POST.get('claim_status'),
            'payment_option': request.POST.get('payment_option'),
            'claim_amount': request.POST.get('claim_amount') or None,
            'claim_created_date': request.POST.get('claim_created_date') or None,
            'linked_email_id': linked_id,
            'vested_pot_available': request.POST.get('vested_pot_available') == 'on',
            'vested_pot_paid_date': request.POST.get('vested_pot_paid_date') or None,
            'savings_pot_available': request.POST.get('savings_pot_available') == 'on',
            'savings_pot_paid_date': request.POST.get('savings_pot_paid_date') or None,
            'infund_cert_date': request.POST.get('infund_cert_date') or None,
        }

        # 1. Save or Update the Claim
        if claim_id:
            AcvvClaim.objects.filter(id=claim_id).update(**data)
            claim_obj = AcvvClaim.objects.get(id=claim_id)
            messages.success(request, f"Claim for {claim_obj.member_surname} updated.")
        else:
            claim_obj = AcvvClaim.objects.create(**data)
            messages.success(request, f"New {claim_type} claim created successfully.")

        # 2. HANDLE CLAIM NOTES & INTERNAL ATTACHMENTS
        note_selection = request.POST.get('note_selection')
        note_description = request.POST.get('note_description')
        internal_attachment = request.FILES.get('claim_attachment')

        if note_selection or note_description or internal_attachment:
            ClaimNote.objects.create(
                claim=claim_obj,
                note_selection=note_selection,
                note_description=note_description,
                attachment=internal_attachment,
                created_by=request.user
            )
            messages.info(request, "Internal claim note saved.")

        # 3. HANDLE OUTGOING EMAIL LOGIC WITH ATTACHMENTS
        recipient = request.POST.get('member_recipient_email')
        subject = request.POST.get('member_email_subject_reply')
        body = request.POST.get('email_body_html_content')
        
        # Capture the specific file meant for the email recipient
        email_attachment = request.FILES.get('email_attachment')

        if recipient and subject and body:
            target_email = settings.OUTLOOK_EMAIL_ADDRESS
            
            # Pass the email_attachment to your outlook service
            result = send_outlook_email(
                target_email, 
                recipient, 
                subject, 
                body, 
                content_type='Html',
                attachment=email_attachment  # Ensure your service is updated to handle this
            )
            
            if result.get('success'):
                # Log the email to branch history
                acvv_record = Globalacvv.objects.filter(mip_names=company_code).first()
                if acvv_record:
                    attach_msg = f" (with attachment: {email_attachment.name})" if email_attachment else ""
                    ClientNotes.objects.create(
                        acvv_record=acvv_record,
                        notes=f"Email Sent: {subject}\nRecipient: {recipient}{attach_msg}",
                        user=request.user.username,
                        date=timezone.now(),
                        communication_type="Email",
                        action_note_type="Correspondence"
                    )
                messages.success(request, f"Email sent successfully to {recipient}.")
            else:
                messages.error(request, f"Email failed: {result.get('error')}")

        # Final Redirects
        if claim_type == 'Two Pot':
            return redirect('global_two_pot')
        return redirect('global_claims')

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from django.utils import timezone
from django.http import HttpResponse

@login_required
def export_global_claims_excel(request):
    """
    Exports claims to the standard Register format (Green Theme) matching the attachment.
    Excludes 'Two Pot' claims.
    """
    query = request.GET.get('q')
    
    # 1. Fetch claims excluding 'Two Pot'
    claims = AcvvClaim.objects.all().exclude(claim_type='Two Pot').order_by('claim_created_date')
    
    if query:
        claims = claims.filter(
            Q(id_number__icontains=query) | 
            Q(member_surname__icontains=query) | 
            Q(company_code__icontains=query)
        )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Claims Register"

    # Define Green Theme Styles (Matching the image)
    green_fill = PatternFill(start_color="C6E0B4", end_color="C6E0B4", fill_type="solid")
    border = Border(left=Side(style='thin'), right=Side(style='thin'), 
                    top=Side(style='thin'), bottom=Side(style='thin'))
    header_font = Font(bold=True, size=11)
    alignment = Alignment(horizontal='center', vertical='center')

    # 2. Header Row Titles (Matching Image: Co Code, Branch, Agent, etc.)
    headers = [
        'Co Code', 'Branch', 'Agent', 'MIP Number', 'ID Number', 
        'Name', 'Surname', 'Type', 'Status', 'Exit Reason', 
        'Created', 'Submitted', 'Paid'
    ]
    
    ws.append(headers)
    
    # Apply styling to headers
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = green_fill
        cell.alignment = alignment
        cell.border = border

    # 3. Data Rows
    for c in claims:
        row = [
            c.company_code,                                      # Co Code
            '',                                                 # Branch (Placeholder if separate)
            c.agent if hasattr(c, 'agent') else '',             # Agent
            c.mip_number if hasattr(c, 'mip_number') else '',   # MIP Number
            c.id_number,                                        # ID Number
            c.member_name,                                      # Name
            c.member_surname,                                   # Surname
            c.claim_type,                                       # Type
            c.claim_status,                                     # Status
            c.exit_reason if hasattr(c, 'exit_reason') else '', # Exit Reason
            c.claim_created_date.strftime('%Y-%m-%d') if c.claim_created_date else '', # Created
            c.date_submitted.strftime('%Y-%m-%d') if hasattr(c, 'date_submitted') and c.date_submitted else '', # Submitted
            c.date_paid.strftime('%Y-%m-%d') if hasattr(c, 'date_paid') and c.date_paid else ''              # Paid
        ]
        ws.append(row)
        
        # Apply borders to the data row
        for cell in ws[ws.max_row]:
            cell.border = border

    # 4. Formatting - Auto-adjust Column Widths
    column_widths = [10, 20, 15, 15, 18, 15, 15, 12, 20, 15, 12, 12, 12]
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
    """
    Displays items marked as 'Deleted' (DLT).
    """
    if request.user.username.lower() != 'omega' and not request.user.is_superuser:
        messages.error(request, "Access restricted.")
        return redirect('dashboard')

    # UPDATED: Filter by the new 'DLT' status and work_related=False
    recycled_items = EmailDelegation.objects.filter(
        status='DLT', 
        work_related=False
    ).order_by('-received_at')
    
    target_email = settings.OUTLOOK_EMAIL_ADDRESS 
    tasks = []

    for item in recycled_items:
        endpoint = f"messages/{item.email_id}?$select=subject,from"
        email_data = _make_graph_request(endpoint, target_email)
        
        if 'error' not in email_data:
            subject = email_data.get('subject')
            sender = email_data.get('from', {}).get('emailAddress', {}).get('name', 'Unknown')
        else:
            subject = "[Email no longer in Outlook]"
            sender = "N/A"

        tasks.append({
            'delegation_id': item.pk,
            'subject': subject,
            'from': sender,
            'received': item.received_at
        })

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
    """View details of a recycled item."""
    delegation = get_object_or_404(EmailDelegation, pk=delegation_id)
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    endpoint = f"messages/{delegation.email_id}"
    email_data = _make_graph_request(endpoint, target_email)

    if 'error' in email_data:
        messages.error(request, "Error fetching email content.")
        return redirect('recycle_bin')

    return render(request, 'acvv_app/view_recycled_item.html', {
        'delegation': delegation,
        'email': email_data
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
    Displays the email content and audit trail. 
    FIXED: Now pulls actual body and attachments for local SENT records.
    """
    import os
    from django.utils.safestring import mark_safe

    # 1. Flexible Lookup (Handles both PK and Microsoft ID)
    if str(delegation_id).isdigit():
        task = get_object_or_404(EmailDelegation, Q(id=delegation_id) | Q(email_id=delegation_id))
    else:
        task = get_object_or_404(EmailDelegation, email_id=delegation_id)

    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    email_content = ""
    attachments = []

    # 2. LOCAL vs MICROSOFT LOGIC
    if task.email_id.startswith('SENT-') or task.email_id.startswith('LOCAL-'):
        # --- NEW: PULL FROM LOCAL DATABASE FIELDS ---
        # We replace the hardcoded "Live version not available" text with your data
        if task.body:
            email_content = task.body
        else:
            email_content = f"<div class='alert alert-warning'><strong>No Body Recorded:</strong> This email was logged with the subject '{task.subject}', but no body content was found.</div>"
        
        # Format the local attachment for the template loop
        if task.attachment:
            attachments = [{
                'name': os.path.basename(task.attachment.name),
                'url': task.attachment.url,
                'contentType': 'application/octet-stream', 
                'is_local': True 
            }]
    else:
        # --- LIVE MICROSOFT FETCH (For original incoming emails) ---
        endpoint = f"messages/{task.email_id}"
        email_data = _make_graph_request(endpoint, target_email)
        
        attachment_endpoint = f"messages/{task.email_id}/attachments"
        attachment_data = _make_graph_request(attachment_endpoint, target_email)
        
        attachments = attachment_data.get('value', [])
        email_content = email_data.get('body', {}).get('content')

    # 3. Fetch local Audit Trail
    actions = DelegationTransactionLog.objects.filter(delegation=task).order_by('transaction_time')

    context = {
        'task': task,
        'email_body': mark_safe(email_content) if email_content else "No content available.",
        'attachments': attachments,
        'actions': actions,
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
    
    # 1. Default to the 1st of the current month
    fiscal_start = today.replace(day=1)

    # 2. Handle GET parameters for Navigation
    req_year = request.GET.get('year')
    req_month = request.GET.get('month')
    
    if req_year and req_month:
        try:
            current_fiscal = datetime.strptime(f"{req_year}-{req_month}-01", '%Y-%m-%d').date()
        except ValueError:
            current_fiscal = fiscal_start
    else:
        current_fiscal = fiscal_start

    # 3. Handle POST Actions (Save/Close)
    if request.method == 'POST':
        if 'save_changes' in request.POST:
            for key, value in request.POST.items():
                if key.startswith('payment_method_'):
                    row_id = key.split('_')[2]
                    # UPDATED: Capture new LPI and Debit Success fields
                    ReconciliationWorksheet.objects.filter(pk=row_id).update(
                        company_status=request.POST.get(f'company_status_{row_id}'),
                        payment_method=request.POST.get(f'payment_method_{row_id}'),
                        arrears=request.POST.get(f'arrears_{row_id}', ''),
                        member_count_reconciled=request.POST.get(f'member_count_{row_id}', 0) or 0,
                        contribution_amount_reconciled=request.POST.get(f'amount_{row_id}', 0.00) or 0.00,
                        
                        # New Fields Added Here
                        lpi_amount=request.POST.get(f'lpi_amount_{row_id}', 0.00) or 0.00,
                        lpi_reason=request.POST.get(f'lpi_reason_{row_id}'),
                        debit_order_success=request.POST.get(f'debit_success_{row_id}'),
                        
                        reconciled_status=request.POST.get(f'recon_status_{row_id}'),
                        date_schedule_received=request.POST.get(f'schedule_{row_id}') or None,
                        date_confirmed_on_step=request.POST.get(f'confirmed_{row_id}') or None,
                        debit_order_date=request.POST.get(f'debit_{row_id}') or None
                    )
            messages.success(request, "Progress saved successfully.")

        elif 'close_month' in request.POST:
            # Close any record matching this year/month
            records_to_update = ReconciliationWorksheet.objects.filter(
                fiscal_month__year=current_fiscal.year, 
                fiscal_month__month=current_fiscal.month
            )
            
            # Update Global Master Note only for those that were successfully reconciled
            for rec in records_to_update:
                if rec.reconciled_status == 'Reconciled':
                    formatted_note_date = current_fiscal.strftime("01.%m.%Y")
                    Globalacvv.objects.filter(mip_names=rec.mg_name).update(notes=formatted_note_date)

            records_to_update.update(is_closed=True, closed_at=timezone.now())
            messages.success(request, f"Fiscal month {current_fiscal.strftime('%B %Y')} closed.")
            return redirect('reconciliation_worksheet')

    # 4. FETCH & AUTO-GENERATE LOGIC
    records = ReconciliationWorksheet.objects.filter(fiscal_month=current_fiscal)
    
    if not records.exists():
        # Check for fallback to 8th
        old_format_date = current_fiscal.replace(day=8)
        records = ReconciliationWorksheet.objects.filter(fiscal_month=old_format_date)
        
        if records.exists():
            current_fiscal = old_format_date
        else:
            # Generate new rows
            base_data = Globalacvv.objects.all() 
            for item in base_data:
                ReconciliationWorksheet.objects.get_or_create(
                    fiscal_month=current_fiscal,
                    mg_name=item.mip_names,
                    mg_code=item.branch_code
                )
            records = ReconciliationWorksheet.objects.filter(fiscal_month=current_fiscal)

    # 5. SUBQUERY LOGIC FOR REQUIREMENTS 11.1 & 11.2
    last_ws_recon_sub = ReconciliationWorksheet.objects.filter(
        mg_name=OuterRef('mg_name'),
        fiscal_month__lt=current_fiscal,
        reconciled_status='Reconciled'
    ).order_by('-fiscal_month').values('fiscal_month')[:1]

    acvv_member_sub = Globalacvv.objects.filter(mip_names=OuterRef('mg_name')).values('member')[:1]
    acvv_notes_sub = Globalacvv.objects.filter(mip_names=OuterRef('mg_name')).values('notes')[:1]

    records = records.annotate(
        acvv_member_count=Subquery(acvv_member_sub),
        master_start_date=Subquery(acvv_notes_sub),
        last_reconciled_ws=Subquery(last_ws_recon_sub)
    )

    # 6. Apply Logic Loop
    for r in records:
        if r.last_reconciled_ws:
            last_date = r.last_reconciled_ws
            r.last_fiscal_display = last_date.strftime("%B %Y")
        elif r.master_start_date:
            try:
                last_date = datetime.strptime(r.master_start_date, "%d.%m.%Y").date()
                r.last_fiscal_display = last_date.strftime("%B %Y")
            except:
                last_date = None
                r.last_fiscal_display = r.master_start_date
        else:
            last_date = None
            r.last_fiscal_display = "No Data"

        if last_date:
            diff = (current_fiscal.year - last_date.year) * 12 + (current_fiscal.month - last_date.month)
            r.is_overdue = diff >= 2
        else:
            r.is_overdue = True

    history = ReconciliationWorksheet.objects.values('fiscal_month').distinct().order_by('-fiscal_month')

    return render(request, 'acvv_app/reconciliation_worksheet.html', {
        'records': records,
        'display_name': current_fiscal.strftime("%B %Y"),
        'history': history,
        'is_closed': records.filter(is_closed=True).exists(),
        'can_close': not records.filter(is_closed=True).exists(),
        'current_fiscal': current_fiscal
    })
    
@login_required
def export_reconciliation_worksheet(request, date_str):
    """
    Exports the reconciliation data to Excel with historical tracking logic.
    """
    try:
        fiscal_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse("Invalid date format", status=400)

    # 1. Mirror the view subqueries
    last_ws_recon_sub = ReconciliationWorksheet.objects.filter(
        mg_name=OuterRef('mg_name'),
        fiscal_month__lt=fiscal_date,
        reconciled_status='Reconciled'
    ).order_by('-fiscal_month').values('fiscal_month')[:1]

    acvv_member_sub = Globalacvv.objects.filter(mip_names=OuterRef('mg_name')).values('member')[:1]
    acvv_notes_sub = Globalacvv.objects.filter(mip_names=OuterRef('mg_name')).values('notes')[:1]

    records = ReconciliationWorksheet.objects.filter(fiscal_month=fiscal_date).annotate(
        acvv_member_count=Subquery(acvv_member_sub),
        master_start_date=Subquery(acvv_notes_sub),
        last_reconciled_ws=Subquery(last_ws_recon_sub)
    )
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Recon {fiscal_date.strftime('%b %Y')}"
    
    headers = [
        "MG Name", "MG Code", "Company Status", "Payment Method", 
        "Last Fiscal Reconciled", "Arrears", "Member Count Reconciled", 
        "Contribution Amount Reconciled", "Reconciled Status", 
        "Date Schedule Received", "Date Confirmed on Step", "Debit order date"
    ]
    ws.append(headers)

    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True)

    for r in records:
        # Status cleaning
        display_status = r.company_status if r.company_status else "Active"
        if display_status.lower() in ['done', 'active']:
            display_status = "Active"

        # Tracking logic for Last Fiscal Reconciled
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
            r.mg_name, r.mg_code, display_status, r.payment_method,
            display_recon, 
            r.arrears,
            r.member_count_reconciled or r.acvv_member_count,
            r.contribution_amount_reconciled, 
            r.reconciled_status,
            r.date_schedule_received, 
            r.date_confirmed_on_step, 
            r.debit_order_date
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
    """
    Standard Reconciliation Export for basic summaries.
    """
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
    View to display only NEW and DELEGATED (DEL) emails with date filtering.
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Filter for NEW and DEL statuses only
    emails = EmailDelegation.objects.filter(
        status__in=['NEW', 'DEL']
    ).select_related('assigned_user').order_by('-received_at')

    # Apply date filters if provided
    if start_date and end_date:
        emails = emails.filter(received_at__date__range=[start_date, end_date])

    # Status counts for badges
    new_count = emails.filter(status='NEW').count()
    del_count = emails.filter(status='DEL').count()

    context = {
        'emails': emails,
        'new_count': new_count,
        'del_count': del_count,
    }
    return render(request, 'acvv_app/outlook_email_list.html', context)

@login_required
def export_email_tasks_excel(request):
    """
    Exports the filtered email task list to Excel.
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    emails = EmailDelegation.objects.filter(status__in=['NEW', 'DEL']).order_by('-received_at')
    
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
    # Handle New Entry Submission
    if request.method == 'POST':
        TempExit.objects.create(
            mg_code=request.POST.get('mg_code'),
            surname=request.POST.get('surname'),
            initials=request.POST.get('initials'),
            mip_no=request.POST.get('mip_no'),
            id_no=request.POST.get('id_no'),
            reason=request.POST.get('reason'),
            bis_from_date=request.POST.get('bis_from') or None,
            bis_end_date=request.POST.get('bis_end') or None,
            full_contributions_start_date=request.POST.get('full_start') or None,
            note=request.POST.get('note')
        )
        messages.success(request, "Temp Exit added successfully.")
        return redirect('temp_exists_list')

    # Display existing entries
    exits = TempExit.objects.all().order_by('-created_at')
    return render(request, 'acvv_app/temp_exists.html', {'exits': exits})

@login_required
def outlook_view_thread(request, delegation_id):
    # 1. Flexible Lookup
    if delegation_id.isdigit():
        task = get_object_or_404(EmailDelegation, Q(id=delegation_id) | Q(email_id=delegation_id))
    else:
        task = get_object_or_404(EmailDelegation, email_id=delegation_id)

    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    email_content = ""
    attachments = []

    # 2. FIX: Check if it is a local "SENT" ID before calling Graph API
    if task.email_id.startswith('SENT-'):
        email_content = f"""
            <div class='alert alert-success'>
                <strong>Local Record:</strong> This email was sent directly from the ACVV App. 
                Microsoft does not provide a live preview for this specific tracking ID.
                <br><small>Subject: {task.subject}</small>
            </div>"""
    else:
        # Only call Graph API for real Microsoft IDs
        endpoint = f"messages/{task.email_id}"
        email_data = _make_graph_request(endpoint, target_email)
        
        attachment_endpoint = f"messages/{task.email_id}/attachments"
        attachment_data = _make_graph_request(attachment_endpoint, target_email)
        attachments = attachment_data.get('value', [])
        email_content = email_data.get('body', {}).get('content')

    # 3. Fetch local Audit Trail
    actions = DelegationTransactionLog.objects.filter(delegation=task).order_by('transaction_time')

    context = {
        'task': task,
        'email_body': mark_safe(email_content) if email_content else "No content available.",
        'attachments': attachments,
        'actions': actions,
    }
    return render(request, 'acvv_app/outlook_view_thread.html', context)

@login_required
def download_acvv_email(request, delegation_id):
    """
    Fetches raw MIME content from Outlook OR generates a local .eml file 
    using the new body and attachment fields in EmailDelegation.
    """
    import requests
    import os
    from django.conf import settings
    from .services.outlook_graph_service import get_current_access_token
    from django.utils.text import slugify
    from email.message import EmailMessage
    from email.utils import make_msgid 

    # 1. ID RESOLUTION
    try:
        if str(delegation_id).isdigit():
            task = get_object_or_404(EmailDelegation, pk=delegation_id)
            ms_id = task.email_id
        else:
            task = get_object_or_404(EmailDelegation, email_id=delegation_id)
            ms_id = delegation_id
    except Exception:
        messages.error(request, "Task record not found.")
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

    # 2. LOCAL GENERATION (For SENT- or LOCAL- IDs)
    if ms_id.startswith('SENT-') or ms_id.startswith('LOCAL-'):
        msg = EmailMessage()
        msg['Subject'] = task.subject
        msg['From'] = task.sender_address or settings.OUTLOOK_EMAIL_ADDRESS
        msg['To'] = "Recipient (Details in App Logs)"
        msg['Date'] = task.received_at.strftime('%a, %d %b %Y %H:%M:%S +0200') if task.received_at else ""
        msg['Message-ID'] = make_msgid()
        
        # --- BODY LOGIC: Pull directly from the task object ---
        # We no longer search ClientNotes; we use the new field we added to the model.
        body_content = task.body if task.body else "Body content not found in record."
        msg.set_content(body_content)

        # --- ATTACHMENT LOGIC: Pull from the task object ---
        if task.attachment:
            try:
                # Resolve the physical file path using .path
                file_path = task.attachment.path
                
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                        file_name = os.path.basename(file_path)
                        
                    # Physically add the binary file to the EML object
                    msg.add_attachment(
                        file_data,
                        maintype='application',
                        subtype='octet-stream',
                        filename=file_name
                    )
            except Exception as e:
                print(f"DEBUG DOWNLOAD ATTACHMENT ERROR: {e}")

        # Return the generated .eml file
        response = HttpResponse(msg.as_bytes(), content_type='message/rfc822')
        response['Content-Disposition'] = f'attachment; filename="SENT_{slugify(task.subject)[:30] or "record"}.eml"'
        return response

    # 3. LIVE MICROSOFT DOWNLOAD (Keep this for real Outlook IDs)
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    access_token = get_current_access_token()
    
    if not access_token:
        messages.error(request, "Authentication failed: Outlook access token missing.")
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

    url = f"https://graph.microsoft.com/v1.0/users/{target_email}/messages/{ms_id}/$value"
    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            django_response = HttpResponse(res.content, content_type='message/rfc822')
            django_response['Content-Disposition'] = f'attachment; filename="{slugify(task.subject)[:50]}.eml"'
            return django_response
    except Exception as e:
        messages.error(request, f"Outlook Error: {e}")

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    
import openpyxl
from openpyxl.styles import PatternFill, Border, Side, Alignment, Font
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Q
from .models import AcvvClaim, Globalacvv

def get_branch_map_acvv(claims_queryset):
    """ Helper to map company codes to formal Branch names for ACVV """
    codes = claims_queryset.values_list('company_code', flat=True).distinct()
    branches = Globalacvv.objects.filter(mip_names__in=codes)
    return {b.mip_names: b.member for b in branches}

@login_required
def export_two_pot_invoice_cecile(request):
    """
    Report 1: Cecile Invoice Format (Grey Theme)
    """
    query = request.GET.get('q')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    claims = AcvvClaim.objects.filter(claim_type='Two Pot').order_by('claim_created_date')
    if query:
        claims = claims.filter(Q(id_number__icontains=query) | Q(member_surname__icontains=query))
    if start_date and end_date:
        claims = claims.filter(claim_created_date__range=[start_date, end_date])

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Cecile Invoice"

    header_fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

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

    for claim in claims:
        initials = "".join([n[0] for n in claim.member_name.split() if n]) if claim.member_name else ""
        is_paid = str(claim.claim_status).upper().strip() == "PAID"
        
        ws.append([
            claim.claim_created_date.strftime('%d/%m/%Y') if claim.claim_created_date else '',
            initials,
            claim.member_surname,
            claim.mip_number,
            claim.id_number,
            claim.company_code,
            branch_map.get(claim.company_code, ""),
            claim.agent or "",
            "yes" if is_paid else "no",
            claim.date_submitted.strftime('%d/%m/%Y') if claim.date_submitted else '',
            "YES" if is_paid else "NO",
            "R37.95",
            "SUBMIT ONLINE"
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="Cecile_Invoice_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    wb.save(response)
    return response

@login_required
def export_two_pot_tracking_acvv(request):
    """
    Report 2: Full Tracking (Yellow Theme) with Red text for 'NO' statuses.
    Matches attached image format.
    """
    query = request.GET.get('q')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    claims_queryset = AcvvClaim.objects.filter(claim_type='Two Pot').order_by('claim_created_date')

    if query:
        claims_queryset = claims_queryset.filter(
            Q(id_number__icontains=query) | Q(member_surname__icontains=query) | 
            Q(company_code__icontains=query) | Q(mip_number__icontains=query)
        )

    if start_date and end_date:
        claims_queryset = claims_queryset.filter(claim_created_date__range=[start_date, end_date])

    branch_map = get_branch_map_acvv(claims_queryset)

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
        "DATE EXTRACT INFO / FORM FROM WEB", "Initials", "Surname", 
        "Member number", "ID NUMBER", "Fund", "Branch", "Query", "Claim", 
        "Qualified", "Date submitted/ online", "Succesfull Loaded confirm", 
        "Amount Apply for", "Admin Fee R33+15%", "Note"
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
        is_paid = str(claim.claim_status).upper().strip() == "PAID"
        qualified_val = "YES" if is_paid else "NO"
        
        if is_paid:
            submit_date_label = claim.date_submitted.strftime('%d.%m.%Y') if claim.date_submitted else "Pending"
        else:
            submit_date_label = "Withdrawal Not Allowed"

        row = [
            claim.claim_created_date.strftime('%d/%m/%Y') if claim.claim_created_date else '',
            initials,
            claim.member_surname,
            claim.mip_number,
            claim.id_number,
            claim.company_code,
            branch_map.get(claim.company_code, "Unknown"),
            "Savings Form Request",
            "Savings Form Submitted" if is_paid else "Member Emergency Savings Pot Withdrawal Requested",
            qualified_val,
            submit_date_label,
            "YES" if is_paid else "",
            float(claim.claim_amount or 0),
            "37.95",
            claim.notes.last().note_description if claim.notes.exists() else ""
        ]
        ws.append(row)

        # Apply Red Text for "NO" status rows
        for cell in ws[ws.max_row]:
            cell.border = thin_border
            cell.alignment = Alignment(vertical='center', horizontal='left')
            if qualified_val == "NO":
                cell.font = Font(size=9, color="FF0000")
            else:
                cell.font = Font(size=9)

    widths = [22, 8, 18, 14, 18, 10, 25, 20, 35, 10, 22, 18, 14, 14, 40]
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
    Now correctly saves body and attachment to EmailDelegation.
    """
    if request.method == 'POST':
        recipient = request.POST.get('member_recipient_email')
        subject = request.POST.get('member_email_subject_reply')
        body = request.POST.get('email_body_html_content')
        attachment = request.FILES.get('email_attachment')

        if recipient and subject and body:
            target_email = settings.OUTLOOK_EMAIL_ADDRESS
            
            # Send via Graph API
            result = send_outlook_email(target_email, recipient, subject, body, content_type='Html', attachment=attachment)
            
            if result.get('success'):
                acvv_record = get_object_or_404(Globalacvv, mip_names=company_code)
                new_ms_id = result.get('message_id') or f"SENT-{timezone.now().timestamp()}"

                # This will no longer throw a TypeError once Step 1 is done!
                EmailDelegation.objects.create(
                    email_id=new_ms_id,
                    subject=subject,
                    body=body, 
                    attachment=attachment,
                    sender_address=target_email,
                    assigned_user=request.user,
                    status='SENT',
                    mip_names=acvv_record.mip_names,
                    received_at=timezone.now(),
                    delegated_at=timezone.now(),
                    work_related=True,
                    communication_type='Email'
                )
                messages.success(request, f"Email sent successfully to {recipient}.")
            else:
                messages.error(request, f"Email failed: {result.get('error')}")

    return redirect('acvv_information', mip_names=company_code)

@login_required
def download_outlook_attachment(request, delegation_id, attachment_id):
    """
    Fetches the attachment from Outlook Graph API, decodes it, and serves it.
    """
    delegation = get_object_or_404(EmailDelegation, pk=delegation_id)
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    
    # Endpoint for a specific attachment
    endpoint = f"messages/{delegation.email_id}/attachments/{attachment_id}"
    attachment_data = _make_graph_request(endpoint, target_email)
    
    if 'error' in attachment_data:
        messages.error(request, "Could not fetch attachment from Outlook.")
        return redirect(request.META.get('HTTP_REFERER', 'outlook_delegated_box'))

    # Microsoft Graph returns file content in base64 format under 'contentBytes'
    file_content = base64.b64decode(attachment_data.get('contentBytes'))
    file_name = attachment_data.get('name', 'attachment')
    content_type = attachment_data.get('contentType', 'application/octet-stream')

    response = HttpResponse(file_content, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response