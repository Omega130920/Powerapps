from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from django.db.models import Q
from django.urls import reverse # Required for clean redirects
from django.conf import settings # Required for target_email default

# Core Django Auth Models
from django.contrib.auth.models import User 

# Local Model Imports
from .models import Globalacvv, ClientNotes, EmailDelegation, DelegationNote, DelegationTransactionLog


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
    """
    Displays the user dashboard, fetches the count of Undelegated-New tasks, 
    and determines the user's access level.
    """
    username = request.user.username
    
    # 🛑 IMPLEMENTATION OF ACCESS CONTROL 🛑
    # Check if the logged-in user is 'omega' or a Django superuser
    is_outlook_admin = request.user.username.lower() == 'omega' or request.user.is_superuser
    
    # Fetch the count of Undelegated - New tasks
    try:
        # Assuming EmailDelegation model is available
        undelegated_count = EmailDelegation.objects.filter(
            status='NEW'
        ).count()
    except Exception as e:
        # Handle case where table might not exist or connection fails
        print(f"Error fetching undelegated count: {e}")
        undelegated_count = 0 
        
    context = {
        'username': username,
        'undelegated_count': undelegated_count, 
        'is_outlook_admin': is_outlook_admin, # <-- PASSING PERMISSION STATUS
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
    Displays the Inbox. Access is restricted to 'omega' or superusers.
    """
    # 🛑 ENFORCEMENT: Restrict access to 'omega' or superusers 🛑
    if request.user.username.lower() != 'omega' and not request.user.is_superuser:
        messages.error(request, "Access restricted. You do not have permission to view the main Outlook Inbox.")
        return redirect('outlook_delegated_box') # Redirect unauthorized users to their delegated queue

    # DELEGATION AWARENESS: Get target email from URL or settings default 
    target_email = request.GET.get('email', settings.OUTLOOK_EMAIL_ADDRESS)
    
    # --- FETCH EMAIL DATA AND JOIN STATUS ---
    context = {
        'target_email': target_email, 
        'messages': [], 
    }
    
    # CORRECTED CALL: Passing target_email as the first argument 
    inbox_data = fetch_inbox_messages(target_email, 20) 
    
    if 'error' not in inbox_data:
        emails = inbox_data.get('value', [])
        email_ids = [email['id'] for email in emails]
        
        # Fetch existing delegation records in one query
        delegation_map = {
            d.email_id: d for d in EmailDelegation.objects.filter(email_id__in=email_ids).select_related('assigned_user')
        }
        
        for email in emails:
            email_id = email['id']
            # Look up existing delegation status
            delegation = delegation_map.get(email_id)
            
            # 🛑 CRITICAL: Capture the received date string for saving 🛑
            received_date_str = email.get('receivedDateTime') 
            
            if not delegation:
                # If no record exists, create a new 'NEW' status record, 
                # passing the received date string to save it to the DB
                delegation = get_or_create_delegation_status(
                    email_id,
                    received_date_str=received_date_str # <-- FIX: Passing the date string
                )
            
            # DATE CONVERSION FIX (for display on this page)
            try:
                if received_date_str:
                    # Ensure parser is imported (from dateutil.parser import parser)
                    email['receivedDateTime'] = parser.isoparse(received_date_str)
            except Exception as e:
                print(f"Error parsing date for email {email_id}: {e}")

            # Assign delegation status fields
            email['delegation_status'] = delegation.get_status_display()
            email['assigned_user'] = delegation.assigned_user.username if delegation.assigned_user else None
            email['delegation_id'] = delegation.pk # Primary key for future reference
            
        context['messages'] = emails

    else:
        context['error'] = f"Error fetching Outlook mail: {inbox_data['error']}"
        context['details'] = inbox_data.get('details', 'Check token manager/logs for more info.')

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
    outlook_delegated_box.html
    Displays the list of emails/tasks delegated to the current user (Status='DEL').
    """
    delegations = get_delegated_emails_for_user(request.user)
    tasks = []
    
    # We need the shared mailbox email to target the Graph API
    target_email = settings.OUTLOOK_EMAIL_ADDRESS 

    for delegation in delegations:
        # Fetch subject/sender details from Graph for display
        endpoint = f"messages/{delegation.email_id}?$select=subject,from,receivedDateTime"
        email_data = _make_graph_request(endpoint, target_email)
        
        if 'error' not in email_data:
            tasks.append({
                'delegation_id': delegation.pk,
                'status': delegation.get_status_display(),
                'subject': email_data.get('subject'),
                'from': email_data.get('from', {}).get('emailAddress', {}).get('name', 'Unknown Sender'),
                'received': email_data.get('receivedDateTime')
            })

    context = {
        'tasks': tasks
    }
    return render(request, 'acvv_app/outlook_delegated_box.html', context)


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

@login_required
def acvv_information(request, mip_names):
    acvv_record = get_object_or_404(Globalacvv, mip_names=mip_names)
    
    if request.method == 'POST':
        note_content = request.POST.get('note_content')
        if note_content:
            ClientNotes.objects.create(
                # Use the new ForeignKey to link the note
                acvv_record=acvv_record,
                notes=note_content,
                user=request.user.username,
                date=datetime.now()
            )
            messages.success(request, "Note added successfully!")
            return redirect(f'/acvv/{acvv_record.mip_names}/#notes-tab')
        else:
            messages.error(request, "Note cannot be empty.")

    # Filter notes using the new ForeignKey field
    notes = ClientNotes.objects.filter(acvv_record=acvv_record).order_by('-date')

    context = {
        'acvv_record': acvv_record,
        'notes': notes,
    }
    return render(request, 'acvv_app/acvv_information.html', context)

@login_required
def outlook_delegate_to(request, email_id):
    """
    Handles the detailed delegation form for classification before assignment.
    """
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    # Note: Ensure User model is imported: from django.contrib.auth.models import User
    available_users = User.objects.filter(is_active=True).exclude(pk=request.user.pk)
    
    # --- Handle Delegation POST Submission ---
    if request.method == 'POST':
        assignee_pk = request.POST.get('agent_name')
        
        # 🛑 Capture ALL classification fields, including MIP Names 🛑
        data_for_delegation = {
            'mip_names': request.POST.get('mip_names'),
            'email_category': request.POST.get('email_category'),
            'work_related': request.POST.get('work_related'),
            'status': request.POST.get('New'),           # Uses the name attribute 'New'
            'comm_type': request.POST.get('email_method'),
        }
        
        if assignee_pk and assignee_pk != '__Select Agent__':
            # NOTE: The delegate_email_task signature must now accept this classification_data
            success, message = delegate_email_task(
                email_id, 
                assignee_pk, 
                request.user, 
                classification_data=data_for_delegation # <-- PASSING ALL DATA
            )
            
            if success:
                messages.success(request, f"Task successfully delegated! {message}")
                return redirect('outlook_dashboard')
            else:
                messages.error(request, message)
        else:
            messages.error(request, "Please select an agent for delegation.")


    # --- Fetch Data for GET Request (Fetching the body content directly) ---
    # Fetch all data needed for the form display (including receivedDateTime)
    endpoint = f"messages/{email_id}" 
    # Ensure _make_graph_request is imported from outlook_graph_service
    email_data = _make_graph_request(endpoint, target_email) 

    if 'error' in email_data:
        messages.error(request, f"Error fetching email content: {email_data.get('error')}")
        return redirect('outlook_dashboard')

    # Get the raw HTML content (for plain text display)
    raw_content = email_data.get('body', {}).get('content', '')
    
    # 🛑 Capture the received date string from the API response 🛑
    received_date_str = email_data.get('receivedDateTime')
    
    # 🛑 Ensure the delegation record is created/updated with the correct date
    #    This is crucial to ensure the received_at field is set on NEW tasks
    #    before delegation occurs. We call the function here for the GET request.
    get_or_create_delegation_status(email_id, received_date_str=received_date_str)
    
    context = {
        'email_id': email_id,
        'email_subject': email_data.get('subject', '(No Subject)'),
        'email_content': raw_content, 
        'attachments': email_data.get('attachments', []),
        'available_users': available_users,
        # NOTE: received_date_str is now handled by the get_or_create function
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