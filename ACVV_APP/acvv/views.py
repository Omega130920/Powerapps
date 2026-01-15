from itertools import count
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

# Local Model Imports
from .models import AcvvClaim, BranchDocument, ClaimNote, Globalacvv, ClientNotes, EmailDelegation, DelegationNote, DelegationTransactionLog, ReconciliationRecord, ReconciliationWorksheet


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
    
    inbox_data = fetch_inbox_messages(target_email, 20) 
    
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

def outlook_delegated_box(request):
    # Fetch delegations assigned to the user with status 'DEL'
    delegations = EmailDelegation.objects.filter(assigned_user=request.user, status='DEL').order_by('-delegated_at')
    tasks = []

    for delegation in delegations:
        tasks.append({
            'delegation_id': delegation.pk,
            'status': delegation.get_status_display(),
            'subject': delegation.subject,
            'from': delegation.sender_address, # Captured from our backfill/sync
            'mg_code': delegation.mip_names,
            'received': delegation.received_at,
            'delegated_at': delegation.delegated_at,
            'email_type': delegation.email_category,
        })

    return render(request, 'acvv_app/outlook_delegated_box.html', {'tasks': tasks})


@login_required
def outlook_delegated_action(request, delegation_id):
    """
    outlook_delegated_action.html
    Allows the assigned user to view the full email, add notes, and reply.
    """
    delegation = get_object_or_404(EmailDelegation, pk=delegation_id)
    
    # 🛑 Authorization check 🛑
    if delegation.assigned_user != request.user:
        messages.error(request, "You are not assigned to this task.")
        return redirect('outlook_delegated_box')

    target_email = settings.OUTLOOK_EMAIL_ADDRESS 

    # --- Handle POST Submissions (Notes and Email Reply) ---
    if request.method == 'POST':
        # 1. Handle Note Submission
        if 'note_content' in request.POST:
            note_content = request.POST.get('note_content')
            success, message = add_delegation_note(delegation_id, request.user, note_content)
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
            return redirect('outlook_delegated_action', delegation_id=delegation_id)
        
        # 2. Handle Reply/Send Email Submission
        if 'reply_recipient' in request.POST:
            recipient = request.POST.get('reply_recipient')
            subject = request.POST.get('reply_subject')
            body = request.POST.get('reply_body')
            
            # 2a. Attempt to send email via Graph API
            result = send_outlook_email(target_email, recipient, subject, body, content_type='Html')
            
            if result.get('success'):
                
                # 🛑 NEW: Log the successful transaction for reporting/auditing 🛑
                log_delegation_transaction(
                    delegation_id, 
                    request.user, 
                    subject, 
                    recipient, 
                    action_type='EMAIL_REPLY'
                )
                
                messages.success(request, f"Reply sent successfully from {target_email} to {recipient}.")
            else:
                error_message = f"Reply failed to send. {result.get('error', 'Unknown API Error')}"
                messages.error(request, error_message)
            
            return redirect('outlook_delegated_action', delegation_id=delegation_id)


    # --- FETCH Data for GET Request (Remains the same) ---
    
    # Fetch full email content from Graph
    endpoint = f"messages/{delegation.email_id}"
    email_data = _make_graph_request(endpoint, target_email)
    
    if 'error' in email_data:
        messages.error(request, f"Error fetching email content: {email_data.get('error')}")
        return redirect('outlook_delegated_box')

    context = {
        'delegation': delegation,
        'email': email_data,
        'notes': delegation.notes.all(), # Access notes via related_name defined in the model
        # Optional: Add transaction log data here if you want to display the history
        # 'transactions': delegation.transactions.all() 
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
    Detailed view for a specific ACVV record.
    UPDATED: Handles Internal Notes, Member Claims, and now PDF Folder Uploads.
    """
    acvv_record = get_object_or_404(Globalacvv, mip_names=mip_names)
    
    if request.method == 'POST':
        # --- 1. HANDLE INTERNAL NOTES ---
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
                    date=datetime.now(),
                    communication_type=comm_type,
                    action_note_type=action_note,
                    attachment=file_url
                )
                messages.success(request, "Internal note added successfully!")
                return redirect(f'/acvv-records/{acvv_record.mip_names}/#notes-tab')

        # --- 2. NEW: HANDLE PDF FOLDER UPLOADS ---
        elif 'upload_pdf' in request.POST:
            pdf_file = request.FILES.get('branch_pdf')
            if pdf_file:
                fs = FileSystemStorage()
                # Store in a branch-specific folder structure for organization
                path = f"branch_docs/{acvv_record.mip_names}/{pdf_file.name}"
                filename = fs.save(path, pdf_file)
                file_url = fs.url(filename)

                # Save metadata to our unmanaged document table
                BranchDocument.objects.create(
                    branch_name=acvv_record.mip_names,
                    file_name=pdf_file.name,
                    file_path=file_url,
                    uploaded_by=request.user.username
                )
                messages.success(request, f"'{pdf_file.name}' added to branch folder.")
                return redirect(f'/acvv-records/{acvv_record.mip_names}/#pdf-upload')

    # --- Fetching data for the page display ---
    notes = ClientNotes.objects.filter(acvv_record=acvv_record).order_by('-date')
    company_claims = AcvvClaim.objects.filter(company_code=mip_names).order_by('-claim_created_date')
    
    # NEW: Fetch documents stored for this specific branch
    branch_docs = BranchDocument.objects.filter(branch_name=mip_names).order_by('-uploaded_at')

    # Combined Email Log Logic
    delegated_logs = EmailDelegation.objects.filter(
        Q(mip_names__icontains=acvv_record.mip_names) | Q(mip_names__icontains=acvv_record.branch_code)
    ).select_related('assigned_user')

    sent_logs = ClientNotes.objects.filter(
        acvv_record=acvv_record,
        notes__icontains="Email Composed" 
    )

    combined_email_log = []

    for log in delegated_logs:
        combined_email_log.append({
            'type': 'ORIGINAL',
            'icon': '📩',
            'badge_color': '#1976d2' if log.status != 'DLT' else '#ef5350', 
            'subject': log.subject or f"[{log.email_category}] Outlook Task",
            'received_at': log.received_at,
            'delegated_at': log.delegated_at,
            'assigned_to': log.assigned_user.username if log.assigned_user else "Unassigned",
            'display_type': log.get_status_display(),
            'actioned_at': None, 
            'email_id': log.id,
            'sort_date': log.received_at or log.delegated_at
        })

    for sent in sent_logs:
        subject_parts = sent.notes.split('\n')
        subject = subject_parts[0].replace("Email Composed: ", "") if subject_parts else "Sent Email"
        
        combined_email_log.append({
            'type': 'DIRECT',
            'icon': '📤',
            'badge_color': '#f57c00',
            'subject': subject,
            'received_at': None,
            'delegated_at': None,
            'assigned_to': sent.user,
            'display_type': 'SENT',
            'actioned_at': sent.date,
            'email_id': None,
            'sort_date': sent.date
        })

    combined_email_log.sort(key=lambda x: x['sort_date'] if x['sort_date'] else datetime.min, reverse=True)

    my_delegated_emails = EmailDelegation.objects.filter(
        assigned_user=request.user, 
        status='DEL'
    ).order_by('-received_at')

    context = {
        'acvv_record': acvv_record,
        'notes': notes,
        'company_claims': company_claims,
        'combined_email_log': combined_email_log, 
        'my_delegated_emails': my_delegated_emails,
        'branch_docs': branch_docs,  # Added to context
    }
    return render(request, 'acvv_app/acvv_information.html', context)

@login_required
def outlook_delegate_to(request, email_id):
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    available_users = User.objects.filter(is_active=True).exclude(pk=request.user.pk)
    acvv_records = Globalacvv.objects.all().values('mip_names', 'branch_code')
    
    endpoint = f"messages/{email_id}" 
    email_data = _make_graph_request(endpoint, target_email) 

    if 'error' in email_data:
        messages.error(request, "Could not fetch email content.")
        return redirect('outlook_dashboard')

    email_subject = email_data.get('subject', '(No Subject)')
    # --- NEW: Extract Sender Address ---
    sender_email = email_data.get('from', {}).get('emailAddress', {}).get('address', '')

    if request.method == 'POST':
        work_related_raw = request.POST.get('work_related')
        is_work_related = (work_related_raw == 'Yes')
        assignee_pk = request.POST.get('agent_name')
        mip_names_value = request.POST.get('mip_names')
        
        data_for_delegation = {
            'mip_names': mip_names_value,
            'subject': email_subject,
            'sender_address': sender_email, # Pass to service if needed
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
            delegation.sender_address = sender_email # Update sender
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
                    # Final database sync for the delegation record
                    EmailDelegation.objects.filter(email_id=email_id).update(
                        work_related=True, 
                        status='DEL',
                        subject=email_subject,
                        sender_address=sender_email # Update sender
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
        'email_sender': sender_email, # Pass to template
        'email_content': email_data.get('body', {}).get('content', ''), 
        'attachments': email_data.get('attachments', []),
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
    if request.method == 'POST':
        claim_id = request.POST.get('claim_id')
        
        # 1. Core Data Extraction
        data = {
            'company_code': company_code,
            'id_number': request.POST.get('id_number'),
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

        # 2. Save or Update the Claim Instance
        if claim_id:
            AcvvClaim.objects.filter(id=claim_id).update(**data)
            claim_instance = AcvvClaim.objects.get(id=claim_id)
            messages.success(request, "Claim updated successfully.")
        else:
            claim_instance = AcvvClaim.objects.create(**data)
            messages.success(request, "New claim created successfully.")

        # 3. Handle Claim Note & File Attachment
        # Note: Ensure you have a related model for notes (e.g., ClaimNote) 
        note_selection = request.POST.get('note_selection')
        note_description = request.POST.get('note_description')
        attachment = request.FILES.get('claim_attachment') # request.FILES is required for file uploads

        if note_selection or note_description or attachment:
            # Import your Note model here if not at the top
            # from .models import ClaimNote 
            claim_instance.notes.create(
                note_selection=note_selection,
                note_description=note_description,
                attachment=attachment,
                created_by=request.user
            )
            messages.info(request, "Claim note added.")

        # 4. Handle Email Composition
        recipient = request.POST.get('member_recipient_email')
        subject = request.POST.get('member_email_subject_reply')
        body = request.POST.get('email_body_html_content')

        if recipient and subject and body:
            target_email = settings.OUTLOOK_EMAIL_ADDRESS
            # Send as HTML to support the formatting from your editor
            result = send_outlook_email(target_email, recipient, subject, body, content_type='Html')
            
            if result.get('success'):
                messages.success(request, f"Email sent successfully to {recipient}.")
            else:
                messages.error(request, f"Claim saved, but email failed: {result.get('error')}")

    # Redirecting back to the branch information page
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
    """Dashboard for all claims EXCEPT Two Pot."""
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

    # --- 1. PRE-FETCH EMAIL CONTENT VIA GRAPH API ---
    delegation_pks = [c.linked_email_id for c in claims if c.linked_email_id]
    if delegation_pks:
        delegations_map = EmailDelegation.objects.in_bulk(list(set(delegation_pks)))
        for claim in claims:
            if claim.linked_email_id:
                try:
                    del_obj = delegations_map.get(int(claim.linked_email_id))
                    if del_obj:
                        endpoint = f"messages/{del_obj.email_id}?$select=subject,from,body,receivedDateTime"
                        email_data = _make_graph_request(endpoint, target_email)
                        if 'error' not in email_data:
                            claim.email_preview_subject = email_data.get('subject')
                            claim.email_preview_sender = email_data.get('from', {}).get('emailAddress', {}).get('address')
                            claim.email_preview_body = email_data.get('body', {}).get('content')
                            claim.email_preview_date = email_data.get('receivedDateTime')
                except: continue

    all_companies = Globalacvv.objects.values('mip_names', 'branch_code')
    my_delegated_emails = EmailDelegation.objects.filter(assigned_user=request.user, status='DEL')

    return render(request, 'acvv_app/global_claims.html', {
        'claims': claims,
        'all_companies': all_companies,
        'my_delegated_emails': my_delegated_emails,
        'is_two_pot_view': False
    })

@login_required
def global_two_pot_view(request):
    """Dedicated Dashboard for ONLY Two Pot claims with Pagination."""
    query = request.GET.get('q')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    target_email = settings.OUTLOOK_EMAIL_ADDRESS

    # Filter for Two Pot only
    base_claims = AcvvClaim.objects.filter(claim_type='Two Pot').order_by('-claim_created_date')

    if query:
        base_claims = base_claims.filter(
            Q(id_number__icontains=query) | 
            Q(member_surname__icontains=query) | 
            Q(company_code__icontains=query)
        )

    if start_date and end_date:
        base_claims = base_claims.filter(claim_created_date__range=[parse_date(start_date), parse_date(end_date)])

    # Pagination
    paginator = Paginator(base_claims, 12) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # --- PRE-FETCH EMAIL CONTENT FOR PAGE ---
    delegation_pks = [c.linked_email_id for c in page_obj if c.linked_email_id]
    if delegation_pks:
        # Map IDs to objects for fast lookup
        delegations_map = EmailDelegation.objects.in_bulk(list(set(delegation_pks)))
        for claim in page_obj:
            if claim.linked_email_id:
                try:
                    del_obj = delegations_map.get(int(claim.linked_email_id))
                    if del_obj:
                        email_data = _make_graph_request(f"messages/{del_obj.email_id}?$select=subject,from,body,receivedDateTime", target_email)
                        if 'error' not in email_data:
                            claim.email_preview_subject = email_data.get('subject')
                            claim.email_preview_sender = email_data.get('from', {}).get('emailAddress', {}).get('address')
                            claim.email_preview_body = email_data.get('body', {}).get('content')
                            claim.email_preview_date = email_data.get('receivedDateTime')
                except: continue

    # Using 'acvv_app/global_claims.html' to avoid TemplateDoesNotExist
    # We pass 'claims': page_obj so the template loop {% for claim in claims %} works
    return render(request, 'acvv_app/global_claims.html', {
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
def save_global_claim(request):
    if request.method == 'POST':
        claim_id = request.POST.get('claim_id')
        
        # 1. Data Extraction (Matching your updated MySQL Schema)
        data = {
            'company_code': request.POST.get('company_code'),
            'agent': request.POST.get('agent'),
            'id_number': request.POST.get('id_number'),
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

        # 2. Save or Update Claim
        if claim_id:
            AcvvClaim.objects.filter(id=claim_id).update(**data)
            claim_obj = AcvvClaim.objects.get(id=claim_id)
            messages.success(request, f"Claim for {data['member_surname']} updated successfully.")
        else:
            claim_obj = AcvvClaim.objects.create(**data)
            messages.success(request, f"New claim created for {data['member_surname']}.")

        # 3. Handle Note Creation & File Upload
        n_desc = request.POST.get('note_description')
        n_sel = request.POST.get('note_selection')
        n_file = request.FILES.get('claim_attachment')

        if n_desc or n_sel or n_file:
            ClaimNote.objects.create(
                claim=claim_obj,
                note_selection=n_sel,
                note_description=n_desc,
                attachment=n_file,
                created_by=request.user
            )

        # 4. Handle Outlook Email Dispatch (Compose Form)
        recipient = request.POST.get('member_recipient_email')
        subject = request.POST.get('member_email_subject_reply')
        body_html = request.POST.get('member_email_body_editor') # Matches your textarea ID

        if recipient and subject and body_html:
            from django.conf import settings
            target_email = settings.OUTLOOK_EMAIL_ADDRESS
            
            # Send via Graph API
            result = send_outlook_email(target_email, recipient, subject, body_html, content_type='Html')
            
            if result.get('success'):
                messages.success(request, f"Email sent to {recipient}.")
            else:
                messages.error(request, f"Claim saved, but email failed: {result.get('error')}")

    # Determine redirect based on claim type to keep user in context
    if data.get('claim_type') == 'Two Pot':
        return redirect('two_pot_global')
    return redirect('global_claims')

import openpyxl
from django.http import HttpResponse
from openpyxl.styles import Font, PatternFill

@login_required
def export_global_claims_excel(request):
    """Exports filtered claims to an Excel spreadsheet."""
    query = request.GET.get('q')
    
    # Filter logic should match your dashboard view
    claims = AcvvClaim.objects.all()
    if query:
        claims = claims.filter(
            Q(id_number__icontains=query) | 
            Q(member_surname__icontains=query) | 
            Q(company_code__icontains=query)
        )
    
    # Create Workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Global Claims"

    # Define Header
    headers = [
        'Company Code', 'Agent', 'ID Number', 'Name', 'Surname', 
        'Claim Type', 'Status', 'Date Created', 'Amount'
    ]
    ws.append(headers)

    # Style Header
    header_fill = PatternFill(start_color="C8E6C9", end_color="C8E6C9", fill_type="solid")
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = header_fill

    # Add Data Rows
    for c in claims:
        ws.append([
            c.company_code,
            c.agent,
            c.id_number,
            c.member_name,
            c.member_surname,
            c.claim_type,
            c.claim_status,
            c.claim_created_date.strftime('%Y-%m-%d') if c.claim_created_date else '',
            float(c.claim_amount) if c.claim_amount else 0.00
        ])

    # Prepare Response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Global_Claims_Export.xlsx"'
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
    Detailed audit trail of a specific email thread.
    Combines Database Logs (Transactions) with Live Graph API data (Body/Attachments).
    """
    # 1. Get the local database record
    task = get_object_or_404(EmailDelegation, pk=delegation_id)
    target_email = settings.OUTLOOK_EMAIL_ADDRESS

    # 2. Fetch live email body from Graph API
    endpoint = f"messages/{task.email_id}"
    email_data = _make_graph_request(endpoint, target_email)
    
    # 3. Fetch live attachments from Graph API
    attachment_endpoint = f"messages/{task.email_id}/attachments"
    attachment_data = _make_graph_request(attachment_endpoint, target_email)
    attachments = attachment_data.get('value', [])

    # 4. Fetch local Audit Trail (Transactions)
    # UPDATED: Changed 'timestamp' to 'transaction_time' to match your model choice
    actions = DelegationTransactionLog.objects.filter(delegation=task).order_by('transaction_time')

    context = {
        'task': task,
        'email_body': email_data.get('body', {}).get('content', 'Content not found.'),
        'attachments': attachments,
        'actions': actions,
    }
    return render(request, 'acvv_app/outlook_view_thread.html', context)

@login_required
def export_temp_exists(request):
    """
    Generates and exports an Excel file with the headers:
    MG Code, Surname, Initials, MIP No., ID No., Reason, 
    BIS From Date, BIS End Date, Full Contributions Start Date, Note
    """
    # Create a new workbook and select the active sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Temp Exists"

    # Define headers based on reference image image_63c381.png
    headers = [
        "MG Code", "Surname", "Initials", "MIP No.", "ID No.", 
        "Reason", "BIS From Date", "BIS End Date", 
        "Full Contributions Start Date", "Note"
    ]

    # Write headers to the first row
    for col_num, header_title in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header_title
        # Optional: Make headers bold
        cell.font = openpyxl.styles.Font(bold=True)

    # Prepare the response
    filename = f"Temp_Exists_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    
    # Save workbook to the response
    wb.save(response)
    return response

@login_required
def reconciliation_worksheet(request):
    today = timezone.now().date()
    
    # 1. Fiscal Month Logic: Cycle runs 8th to 7th
    if today.day < 8:
        fiscal_start = (today - relativedelta(months=1)).replace(day=8)
    else:
        fiscal_start = today.replace(day=8)

    # 2. Allow viewing historical months via GET parameter
    selected_month = request.GET.get('month', fiscal_start.strftime('%Y-%m-%d'))
    try:
        current_fiscal = datetime.strptime(selected_month, '%Y-%m-%d').date()
    except ValueError:
        current_fiscal = fiscal_start

    # 3. Handle POST Actions (Save Changes or Close Off)
    if request.method == 'POST':
        # --- SAVE PROGRESS LOGIC ---
        if 'save_changes' in request.POST:
            # Loop through all items in the POST data to find row IDs
            for key, value in request.POST.items():
                if key.startswith('arrears_'):
                    row_id = key.split('_')[1]
                    
                    # Get values using the unique row ID
                    arrears = request.POST.get(f'arrears_{row_id}')
                    count = request.POST.get(f'count_{row_id}', 0)
                    amount = request.POST.get(f'amount_{row_id}', 0.00)
                    status = request.POST.get(f'status_{row_id}')
                    schedule = request.POST.get(f'schedule_{row_id}')
                    
                    # Update the specific row
                    ReconciliationWorksheet.objects.filter(pk=row_id).update(
                        arrears=arrears,
                        member_count_reconciled=count or 0,
                        contribution_amount_reconciled=amount or 0.00,
                        reconciled_status=status,
                        date_schedule_received=schedule if schedule else None
                    )
            messages.success(request, "Progress saved successfully.")

        # --- CLOSE OFF LOGIC ---
        elif 'close_month' in request.POST:
            ReconciliationWorksheet.objects.filter(fiscal_month=current_fiscal).update(
                is_closed=True, 
                closed_at=timezone.now()
            )
            messages.success(request, f"Fiscal month {current_fiscal.strftime('%B %Y')} closed.")
            return redirect('reconciliation_worksheet')

    # 4. Auto-generate rows if they don't exist
    records = ReconciliationWorksheet.objects.filter(fiscal_month=current_fiscal)
    
    if not records.exists() and current_fiscal == fiscal_start:
        base_data = Globalacvv.objects.all() 
        for item in base_data:
            ReconciliationWorksheet.objects.get_or_create(
                fiscal_month=current_fiscal,
                mg_name=item.mip_names,
                mg_code=item.branch_code
            )
        records = ReconciliationWorksheet.objects.filter(fiscal_month=current_fiscal)

    # 5. History and Context
    history = ReconciliationWorksheet.objects.values('fiscal_month').distinct().order_by('-fiscal_month')

    return render(request, 'acvv_app/reconciliation_worksheet.html', {
        'records': records,
        'display_name': current_fiscal.strftime("%B %Y"),
        'history': history,
        'is_closed': records.filter(is_closed=True).exists(),
        'can_close': today.day >= 8 and not records.filter(is_closed=True).exists(),
        'current_fiscal': current_fiscal # 🛑 FIX: Passes variable to fix NoReverseMatch
    })

@login_required
def export_reconciliation_worksheet(request, date_str):
    """
    Exports the reconciliation data to Excel with all 12 required columns.
    """
    try:
        fiscal_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse("Invalid date format", status=400)

    records = ReconciliationWorksheet.objects.filter(fiscal_month=fiscal_date)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Recon {fiscal_date.strftime('%b %Y')}"
    
    # Updated Headers based on your specific requirements (image_644bc3.png)
    headers = [
        "MG Name", "MG Code", "Company Status", "Payment Method", 
        "Last Fiscal Reconciled", "Arrears", "Member Count Reconciled", 
        "Contribution Amount Reconciled", "Reconciled Status", 
        "Date Schedule Received", "Date Confirmed on Step", "Debit order date"
    ]
    ws.append(headers)

    # Bold the headers
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True)

    for r in records:
        ws.append([
            r.mg_name, 
            r.mg_code, 
            r.company_status, 
            r.payment_method,
            r.last_fiscal_reconciled, 
            r.arrears, 
            r.member_count_reconciled,
            r.contribution_amount_reconciled, 
            r.reconciled_status,
            r.date_schedule_received, 
            r.date_confirmed_on_step, 
            r.debit_order_date
        ])
        
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = f'attachment; filename="Reconciliation_Worksheet_{date_str}.xlsx"'
    wb.save(response)
    return response
    
@login_required
def export_reconciliation(request, date_str):
    fiscal_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    records = ReconciliationRecord.objects.filter(fiscal_month=fiscal_date)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Recon {fiscal_date.strftime('%b %Y')}"
    
    # Set headers
    headers = ["Member Group", "Branch Code", "Billed", "Paid", "Outstanding", "Note"]
    ws.append(headers)
    
    # Style headers
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True)

    for r in records:
        ws.append([r.mip_name, r.branch_code, r.billed_amount, r.paid_amount, r.outstanding_amount, r.note])
        
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f'attachment; filename="Reconciliation_{date_str}.xlsx"'
    wb.save(response)
    return response

@login_required
def outlook_email_list(request):
    """
    View to display only NEW and DELEGATED (DEL) emails.
    """
    # Filter for NEW and DEL statuses only
    emails = EmailDelegation.objects.filter(
        status__in=['NEW', 'DEL']
    ).select_related('assigned_user').order_by('-received_at')

    # Status counts for badges
    new_count = emails.filter(status='NEW').count()
    del_count = emails.filter(status='DEL').count()

    context = {
        'emails': emails,
        'new_count': new_count,
        'del_count': del_count,
    }
    return render(request, 'acvv_app/outlook_email_list.html', context)