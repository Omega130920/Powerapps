import base64
from datetime import date
from time import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import logging
from django.db.models import Q
import pandas as pd
from django.db import transaction
from dateutil.relativedelta import relativedelta
from django.core.paginator import Paginator
from datetime import datetime
from .services.outlook_graph_service import OutlookGraphService

logger = logging.getLogger(__name__)

# Import your unmanaged models
from .models import PssubfBeneficiary, PssubfDirectEmail, PssubfInbox, PssubfDelegate, PssubfAction, PssubfNote, PssubfProfileNote
# Import your verified services
from PSSUBF_APP.services.outlook_graph_service import OutlookGraphService
from PSSUBF_APP.services.delegation_service import delegate_pssubf_task

@login_required
def pssubf_switchboard(request):
    """
    Main Menu / Switchboard.
    Mapped to path('')
    Renders the card-based navigation (dashboard.html).
    """
    return render(request, 'pssubf/dashboard.html')

@login_required
def pssubf_dashboard(request):
    """
    Fetches data directly from the local pssubf_inbox database table 
    instead of the live Outlook Graph API.
    """
    # 1. Pull directly from your Local DB Model
    # This matches your PssubfInbox model defined with managed=False
    inbox_items = PssubfInbox.objects.all().order_by('-received_timestamp')

    # 2. Render to your template
    return render(request, 'pssubf/inbox_list.html', {
        'inbox_items': inbox_items
    })

@login_required
def pssubf_delegate_view(request, email_id):
    """View to fetch live email details, resolve inline images, and delegate to an agent."""
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    
    # 1. Fetch local record: This is the anchor for your "Email Received" date
    inbox_item = PssubfInbox.objects.filter(email_id=email_id).first()
    
    # Get list of agents for the dropdown
    available_users = User.objects.filter(is_active=True)

    if request.method == 'POST':
        agent_name = request.POST.get('assigned_agent')
        is_recycle = 'recycle' in request.POST
        
        success, message = delegate_pssubf_task(
            email_id=email_id,
            agent_name=agent_name,
            delegator_user=request.user,
            form_data=request.POST,
            is_recycle=is_recycle
        )
        
        if success:
            messages.success(request, message)
            return redirect('pssubf_dashboard')
        else:
            messages.error(request, f"Error: {message}")

    # Fetch live content from Graph API
    email_data = OutlookGraphService._make_graph_request(f"messages/{email_id}", method='GET')
    
    # Error handling and variable assignment for the template
    if isinstance(email_data, dict) and 'error' in email_data:
        email_subject = inbox_item.subject if inbox_item else "Error Fetching Subject"
        email_content = inbox_item.snippet if inbox_item else "Live content unavailable."
        attachments = []
    else:
        email_subject = email_data.get('subject', '(No Subject)')
        email_content = email_data.get('body', {}).get('content', '')
        
        # Fetch Attachments
        attachments = OutlookGraphService.fetch_attachments(target_email, email_id)
        
        # Resolve Inline Images
        for att in attachments:
            if att.get('isInline') and att.get('contentId'):
                cid = att.get('contentId')
                raw = OutlookGraphService.get_attachment_raw(target_email, email_id, att['id'])
                if raw and isinstance(raw, dict) and 'contentBytes' in raw:
                    base64_data = raw['contentBytes']
                    content_type = att.get('contentType', 'image/png')
                    data_url = f"data:{content_type};base64,{base64_data}"
                    email_content = email_content.replace(f"cid:{cid}", data_url)
                    att['contentBytes'] = base64_data
            
            elif 'image' in att.get('contentType', '').lower() and not att.get('contentBytes'):
                raw = OutlookGraphService.get_attachment_raw(target_email, email_id, att['id'])
                if raw and isinstance(raw, dict) and 'contentBytes' in raw:
                    att['contentBytes'] = raw['contentBytes']

    # We return inbox_item so your "Email Received" date is always available
    return render(request, 'pssubf/delegate.html', {
        'email_id': email_id,
        'email_subject': email_subject,
        'email_content': email_content,
        'attachments': attachments,
        'available_users': available_users,
        'inbox_item': inbox_item  # This carries the received_timestamp
    })

@login_required
def pssubf_action_view(request, email_id):
    """
    Agent Action View: Handles Notes, Metadata Updates, Completion, 
    and Email Replies while resolving broken inline images.
    """
    task = get_object_or_404(PssubfDelegate, email_id=email_id)
    target_email = settings.OUTLOOK_EMAIL_ADDRESS 

    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        # 1. Update Metadata
        if action_type == 'update_metadata':
            task.member_group_code = request.POST.get('member_group_code')
            task.email_category = request.POST.get('email_category')
            task.status = request.POST.get('status')
            task.save()
            
            PssubfAction.objects.create(
                task_email_id=email_id,
                action_user=request.user.username,
                action_type="METADATA_UPDATE",
                note_content=f"Updated: Category={task.email_category}, Group={task.member_group_code}, Status={task.status}"
            )
            messages.success(request, "Task information updated successfully.")

        # 2. Add Internal Note (UPDATED to include Status/Classification and PssubfNote saving)
        elif action_type == 'add_note':
            note_text = request.POST.get('note_content')
            
            # Capture the confirmation dropdowns from the note form
            new_category = request.POST.get('email_category')
            new_status = request.POST.get('status')
            
            # Sync the main task state
            if new_category:
                task.email_category = new_category
            if new_status:
                task.status = new_status
            task.save()

            # Save to the new unmanaged table: pssubf_notes
            PssubfNote.objects.create(
                task_email_id=email_id,
                agent_name=request.user.username,
                note_text=note_text,
                classification_at_time=task.email_category,
                status_at_time=task.status
            )

            # Keep the existing PssubfAction log for the timeline
            PssubfAction.objects.create(
                task_email_id=email_id,
                action_user=request.user.username,
                action_type="NOTE",
                note_content=note_text
            )
            messages.success(request, "Internal note saved and task status synchronized.")

        # 3. Handle External Email Reply
        elif action_type == 'send_reply':
            recipient = request.POST.get('reply_recipient')
            subject = request.POST.get('reply_subject')
            body_content = request.POST.get('reply_body')
            
            uploaded_files = request.FILES.getlist('reply_attachments')
            attachments_payload = []
            
            for f in uploaded_files:
                try:
                    content_bytes = f.read()
                    encoded_content = base64.b64encode(content_bytes).decode('utf-8')
                    attachments_payload.append({
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": f.name,
                        "contentType": f.content_type,
                        "contentBytes": encoded_content
                    })
                except Exception as e:
                    logger.error(f"Attachment encoding error: {e}")

            response = OutlookGraphService.send_outlook_email(
                sender=target_email,
                recipient=recipient,
                subject=subject,
                body=body_content,
                attachments=attachments_payload
            )

            if isinstance(response, dict) and 'error' in response:
                messages.error(request, f"Email failed: {response.get('error')}")
            else:
                PssubfAction.objects.create(
                    task_email_id=email_id,
                    action_user=request.user.username,
                    action_type="EMAIL_REPLY",
                    note_content=f"Sent reply to {recipient} with {len(uploaded_files)} files."
                )
                messages.success(request, "Reply sent and logged.")

        # 4. Mark as Complete
        elif action_type == 'mark_complete':
            task.status = 'Completed'
            task.save()
            
            PssubfAction.objects.create(
                task_email_id=email_id,
                action_user=request.user.username,
                action_type="COMPLETED",
                note_content="Agent marked task as completed."
            )
            messages.success(request, "Task closed.")
            return redirect('pssubf_delegations_list')

        return redirect('pssubf_action', email_id=email_id)

    # --- GET Logic: Fetch context for the page ---
    email_data = OutlookGraphService._make_graph_request(f"messages/{email_id}", method='GET')
    attachments = OutlookGraphService.fetch_attachments(target_email, email_id)
    email_content = email_data.get('body', {}).get('content', 'Content unavailable.')

    for att in attachments:
        if att.get('isInline') and att.get('contentId'):
            cid = att.get('contentId')
            raw = OutlookGraphService.get_attachment_raw(target_email, email_id, att['id'])
            if raw and isinstance(raw, dict) and 'contentBytes' in raw:
                base64_data = raw['contentBytes']
                content_type = att.get('contentType', 'image/png')
                data_url = f"data:{content_type};base64,{base64_data}"
                email_content = email_content.replace(f"cid:{cid}", data_url)
                att['contentBytes'] = base64_data

    history = PssubfAction.objects.filter(task_email_id=email_id).order_by('-action_timestamp')

    return render(request, 'pssubf/action_detail.html', {
        'task': task,
        'email_subject': email_data.get('subject', task.subject or '(No Subject)'),
        'email_content': email_content,
        'attachments': attachments,
        'history': history,
        'email_id': email_id
    })

import re # Add to imports

@login_required
def pssubf_view_thread(request, email_id):
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    email_data = OutlookGraphService._make_graph_request(f"messages/{email_id}", method='GET')
    
    email_body = email_data.get('body', {}).get('content', '')
    attachments = OutlookGraphService.fetch_attachments(target_email, email_id)

    # 🚀 FIX: Replace CID with Base64 for inline images
    for att in attachments:
        # Check if it's an inline attachment with a Content-ID
        if att.get('isInline') and att.get('contentId'):
            cid = att.get('contentId')
            # Fetch the raw content if not already present
            raw_data = OutlookGraphService.get_attachment_raw(target_email, email_id, att['id'])
            if raw_data and 'contentBytes' in raw_data:
                base64_data = raw_data['contentBytes']
                content_type = att.get('contentType', 'image/png')
                
                # Replace src="cid:..." with src="data:image/png;base64,..."
                data_url = f"data:{content_type};base64,{base64_data}"
                email_body = email_body.replace(f"cid:{cid}", data_url)

    actions = PssubfAction.objects.filter(task_email_id=email_id).order_by('-action_timestamp')

    return render(request, 'pssubf/thread_history.html', {
        'email_id': email_id,
        'email_subject': email_data.get('subject', 'No Subject'),
        'sender_name': email_data.get('from', {}).get('emailAddress', {}).get('name', 'Unknown'),
        'sender_email': email_data.get('from', {}).get('emailAddress', {}).get('address', ''),
        'email_body': email_body, # Now contains embedded images
        'attachments': attachments,
        'actions': actions
    })

@login_required
def download_pssubf_attachment(request, message_id, attachment_id):
    """Downloads raw file from Outlook Graph API."""
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    raw_data = OutlookGraphService.get_attachment_raw(target_email, message_id, attachment_id)
    
    if not raw_data or 'contentBytes' not in raw_data:
        raise Http404("Attachment not found.")
    
    file_content = base64.b64decode(raw_data['contentBytes'])
    response = HttpResponse(file_content, content_type=raw_data.get('contentType', 'application/octet-stream'))
    response['Content-Disposition'] = f'attachment; filename="{raw_data.get("name", "download")}"'
    return response

@login_required
def sync_pssubf_inbox(request):
    """Triggers the Outlook Graph API to fetch latest mail and save to MySQL."""
    try:
        # This calls your service logic to fetch and save to pssubf_inbox
        new_emails = OutlookGraphService.sync_latest_emails() 
        messages.success(request, f"Successfully synced {len(new_emails)} new emails.")
    except Exception as e:
        messages.error(request, f"Sync failed: {str(e)}")
    
    return redirect('pssubf_dashboard')

@login_required
def pssubf_delegations_list(request):
    """
    Displays the active queue. 
    EXCLUDES items marked as 'Recycled' so they only show in the Recycle Bin.
    """
    # We exclude 'Recycled' to keep this list strictly for work tasks
    delegations = PssubfDelegate.objects.exclude(status='Recycled').order_by('-created_at')
    
    return render(request, 'pssubf/delegations_list.html', {
        'delegations': delegations
    })
    
@login_required
def pssubf_audit_logs(request):
    """The Master Archive / Audit Log view."""
    logs = PssubfAction.objects.all().order_by('-action_timestamp')
    return render(request, 'pssubf/audit_logs.html', {
        'logs': logs
    })
    
@login_required
def pssubf_recycle_bin(request):
    """
    Displays all items marked as 'Recycled'.
    Matches the status value found in the pssubf_delegate table.
    """
    # Changed filter from 'DLT' to 'Recycled' to match your DB screenshot
    recycled_tasks = PssubfDelegate.objects.filter(status='Recycled').order_by('-created_at')
    
    return render(request, 'pssubf/recycle_bin.html', {
        'recycled_tasks': recycled_tasks
    })

@login_required
def pssubf_restore_item(request, email_id):
    """
    Restores an item from the Recycle Bin back to the main Inbox/Queue.
    """
    task = get_object_or_404(PssubfDelegate, email_id=email_id)
    task.status = 'Pending'  # Or 'NEW' depending on your naming convention
    task.save()
    
    # Log the restoration
    PssubfAction.objects.create(
        task_email_id=email_id,
        action_user=request.user.username,
        action_type="RESTORE",
        note_content="Item restored from Recycle Bin to active queue."
    )
    
    messages.success(request, "Item successfully restored.")
    return redirect('pssubf_recycle_bin')

@login_required
def pssubf_audit_logs(request):
    """
    Master Audit Log: Shows New, Delegated, and Completed actions.
    EXCLUDES all Recycle actions to keep the focus on productive workflows.
    """
    query = request.GET.get('q')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # 1. Start with all logs
    # 2. Exclude 'Recycle' action types and 'RESTORE' if you want a clean work log
    logs = PssubfAction.objects.exclude(action_type__in=['Recycle', 'RESTORE'])

    # Apply Search Filter (User, Type, or Content)
    if query:
        logs = logs.filter(
            Q(action_user__icontains=query) |
            Q(action_type__icontains=query) |
            Q(note_content__icontains=query)
        )

    # Apply Date Range Filters
    if start_date:
        logs = logs.filter(action_timestamp__date__gte=start_date)
    if end_date:
        logs = logs.filter(action_timestamp__date__lte=end_date)

    logs = logs.order_by('-action_timestamp')

    return render(request, 'pssubf/audit_logs.html', {
        'logs': logs,
        'query': query,
        'start_date': start_date,
        'end_date': end_date
    })
    
@login_required
def pssubf_recycle_view(request, email_id):
    """View to review recycled item details with fixed inline images before restoration."""
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    # Fetch from delegate table where status is Recycled
    task = get_object_or_404(PssubfDelegate, email_id=email_id, status='Recycled')

    # Fetch live content from Graph API
    email_data = OutlookGraphService._make_graph_request(f"messages/{email_id}", method='GET')
    
    if isinstance(email_data, dict) and 'error' in email_data:
        email_subject = task.subject or "Subject Unavailable"
        email_content = "Live content unavailable (Email may have been moved or deleted in Outlook)."
        attachments = []
    else:
        email_subject = email_data.get('subject', task.subject)
        email_content = email_data.get('body', {}).get('content', '')
        
        # Fetch Attachments
        attachments = OutlookGraphService.fetch_attachments(target_email, email_id)
        
        # 🚀 FIX: Resolve Inline Images (Signatures, etc.)
        for att in attachments:
            # Handle inline images for the email body
            if att.get('isInline') and att.get('contentId'):
                cid = att.get('contentId')
                raw = OutlookGraphService.get_attachment_raw(target_email, email_id, att['id'])
                if raw and isinstance(raw, dict) and 'contentBytes' in raw:
                    base64_data = raw['contentBytes']
                    content_type = att.get('contentType', 'image/png')
                    
                    # Replace CID link with Base64 Data URI
                    data_url = f"data:{content_type};base64,{base64_data}"
                    email_content = email_content.replace(f"cid:{cid}", data_url)
                    
                    # Attach bytes to object for display in the attachment list
                    att['contentBytes'] = base64_data
            
            # Fetch thumbnails for standard image attachments
            elif 'image' in att.get('contentType', '').lower() and not att.get('contentBytes'):
                raw = OutlookGraphService.get_attachment_raw(target_email, email_id, att['id'])
                if raw and isinstance(raw, dict) and 'contentBytes' in raw:
                    att['contentBytes'] = raw['contentBytes']

    return render(request, 'pssubf/recycle_detail.html', {
        'task': task,
        'email_id': email_id,
        'email_subject': email_subject,
        'email_content': email_content,
        'attachments': attachments
    })
    
@login_required
def pssubf_delete_permanent(request, email_id):
    """Permanently deletes a single record from the database."""
    task = get_object_or_404(PssubfDelegate, email_id=email_id)
    task.delete()
    
    # Also clean up the inbox status if needed, or just leave it
    PssubfInbox.objects.filter(email_id=email_id).update(status='DELETED')
    
    messages.error(request, "Record permanently deleted.")
    return redirect('pssubf_recycle_bin')

@login_required
def pssubf_bulk_delete(request):
    """Handles multiple deletions at once."""
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_ids')
        if selected_ids:
            # Delete from delegate table
            PssubfDelegate.objects.filter(email_id__in=selected_ids).delete()
            # Mark as deleted in inbox
            PssubfInbox.objects.filter(email_id__in=selected_ids).update(status='DELETED')
            messages.error(request, f"Permanently deleted {len(selected_ids)} records.")
            
    return redirect('pssubf_recycle_bin')

@login_required
def pssubf_history_preview(request, email_id):
    """
    AJAX View: Finds the sender of the current email and returns 
    all previous delegation records for that sender.
    """
    # 1. Get the current email from the inbox to identify the sender
    # We use .first() to avoid a 404 if the sync hasn't hit the DB yet
    current_mail = PssubfInbox.objects.filter(email_id=email_id).first()
    
    if not current_mail:
        # If not in local DB, we try to get the sender from the Graph API live
        email_data = OutlookGraphService._make_graph_request(f"messages/{email_id}", method='GET')
        sender_email = email_data.get('from', {}).get('emailAddress', {}).get('address', '')
    else:
        sender_email = current_mail.sender

    # 2. Find all previous delegations for this specific sender
    # We look in PssubfDelegate to see who worked on this person's files before
    previous_tasks = PssubfDelegate.objects.filter(
        sender=sender_email
    ).exclude(email_id=email_id).order_by('-created_at')

    context = {
        'sender_email': sender_email,
        'previous_tasks': previous_tasks,
    }

    # 3. Render the partial HTML that "pops up" in the modal
    return render(request, 'pssubf/partials/history_preview_content.html', context)

from django.db import connection # Import this at the top

@login_required
def beneficiary_import_view(request):
    if request.method == 'POST' and request.FILES.get('file'):
        excel_file = request.FILES['file']
        
        try:
            # Read as string to preserve IDs, then handle the "nan" values
            df = pd.read_excel(excel_file, dtype=str)
            df.columns = [c.strip() for c in df.columns]
            
            total_excel_rows = len(df)
            created_count = 0
            updated_count = 0
            import_errors = []

            with transaction.atomic():
                for index, row in df.iterrows():
                    
                    def to_date(val):
                        # Handle various "null" string versions from Excel/Pandas
                        s_val = str(val).strip().lower()
                        if pd.isna(val) or s_val in ['', 'nan', 'none', 'null']: 
                            return None
                        try: 
                            return pd.to_datetime(val).date()
                        except: 
                            return None

                    def to_float(val):
                        # FIXED: Specifically check for "nan" string before conversion
                        s_val = str(val).strip().lower()
                        if pd.isna(val) or s_val in ['', 'nan', 'none', 'null']:
                            return 0.00
                        try:
                            clean_val = s_val.replace(',', '').replace('r', '').strip()
                            return float(clean_val)
                        except: 
                            return 0.00

                    # Identification
                    m_no = str(row.get('Membership Number', '')).strip()
                    id_no = str(row.get('ID Number', '')).strip()

                    if not m_no or m_no.lower() == 'nan':
                        continue

                    try:
                        dob = to_date(row.get('DOB'))
                        cessation = dob + relativedelta(years=18) if dob else None

                        beneficiary_data = {
                            'old_membership_number': row.get('Old membership Number'),
                            'title': row.get('Title'),
                            'initials': row.get('Initials'),
                            'first_name': row.get('First Name'),
                            'second_name': row.get('Second Name'),
                            'last_name': row.get('Last Name'),
                            'id_number': id_no,
                            'dob': dob,
                            'cessation_date': cessation,
                            'gender': row.get('Gender'),
                            'employee_number': row.get('Employee Number'),
                            'fund_join_date': to_date(row.get('Fund Join Date')),
                            'stipened_frequency': row.get('Stipened Frequency'),
                            'stipened': to_float(row.get('Stipened')), # Now safe from "nan"
                            'mobile_1': row.get('Mobile 1'),
                            'email_1': row.get('Email 1'),
                            'mobile_2': row.get('Mobile 2'),
                            'email_2': row.get('Email 2'),
                            'mobile_3': row.get('Mobile 3'),
                            'email_3': row.get('Email 3'),
                            'guardian_mobile': row.get('Guardian Mobile'),
                            'guardian_email': row.get('Guaridan Email'),
                            'guardian_title': row.get('Guardian Title'),
                            'guardian_first_name': row.get('Guardian First Name'),
                            'guardian_second_name': row.get('Guardian Second Name'),
                            'guardian_last_name': row.get('Guardian Last Name'),
                            'guardian_initial': row.get('Guardian Initial'),
                            'guardian_dob': to_date(row.get('Guardian DOB')),
                            'guardian_id_number': row.get('Guardian ID Number'),
                            'guardian_id_type': row.get('Guardian ID Type'),
                            'guardian_gender': row.get('Guardian Gender'),
                            'guardian_address': row.get('Guardian Address'),
                        }

                        # Data Cleanup: Remove keys that are None if they are not allowed in DB
                        # (Membership Number and ID Number are handled separately)
                        beneficiary_data = {k: v for k, v in beneficiary_data.items() if pd.notnull(v) or v is None}

                        obj, created = PssubfBeneficiary.objects.update_or_create(
                            membership_number=m_no,
                            defaults=beneficiary_data
                        )
                        
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1

                    except Exception as e:
                        import_errors.append({"row": index + 2, "m_no": m_no, "reason": str(e)})

            # Session data for the list view
            request.session['import_stats'] = {
                'total': total_excel_rows,
                'created': created_count,
                'updated': updated_count,
                'failed': len(import_errors)
            }
            request.session['import_errors'] = import_errors
            
            return redirect('beneficiary_list')

        except Exception as e:
            messages.error(request, f"File Error: {str(e)}")

    return render(request, 'pssubf/beneficiary_import.html')

@login_required
def beneficiary_list_view(request):
    # 1. Get all records
    queryset = PssubfBeneficiary.objects.all().order_by('last_name')

    # 2. Filter Logic (Age Status)
    status_filter = request.GET.get('status')
    today = date.today()

    if status_filter == 'expired':
        # Members 18 and older
        queryset = queryset.filter(cessation_date__lte=today)
    elif status_filter == 'active':
        # Members under 18
        queryset = queryset.filter(cessation_date__gt=today)

    # 3. Pagination (36 per page)
    paginator = Paginator(queryset, 36)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 4. Handle Session Errors
    import_errors = request.session.pop('import_errors', [])
    
    return render(request, 'pssubf/beneficiary_list.html', {
        'page_obj': page_obj,  # We use page_obj in the loop now
        'import_errors': import_errors,
        'current_status': status_filter,
        'total_count': queryset.count()
    })

from django.utils import timezone  # Ensure this is at the top of your file

from django.utils import timezone # Ensure this is at the top of your views.py

@login_required
def beneficiary_details_view(request, membership_number):
    member = get_object_or_404(PssubfBeneficiary, membership_number=membership_number)
    
    if request.method == 'POST':
        # --- 1. HANDLE DIRECT EMAIL (COMPOSITION TAB) ---
        if request.POST.get('action') == 'send_direct_email':
            recipient = request.POST.get('to_email')
            subject = request.POST.get('subject')
            body_html = request.POST.get('email_html_content')

            if recipient and subject and body_html:
                result = OutlookGraphService.send_outlook_email(settings.OUTLOOK_EMAIL_ADDRESS, recipient, subject, body_html)
                
                if result.get('success') or result == {}:
                    PssubfDirectEmail.objects.create(
                        membership_number=membership_number,
                        agent_name=request.user.username,
                        recipient=recipient,
                        subject=subject,
                        body_html=body_html
                    )
                    PssubfAction.objects.create(
                        task_email_id=f"DIRECT_{membership_number}",
                        action_type="Direct Email Sent",
                        action_user=request.user.username,
                        note_content=f"Sent to: {recipient} | Subject: {subject}",
                        action_timestamp=timezone.now()
                    )
                    messages.success(request, f"Direct email sent successfully to {recipient}.")
                else:
                    messages.error(request, f"Email failed to send: {result.get('error')}")
            return redirect('beneficiary_details', membership_number=membership_number)

        # --- 2. HANDLE GENERAL NOTES (NOTES TAB) ---
        # Changed 'elif' to 'if' and verified the button name matches 'save_note'
        elif 'save_note' in request.POST:
            note_text = request.POST.get('note_text')
            if note_text:
                PssubfProfileNote.objects.create(
                    membership_number=membership_number,
                    agent_name=request.user.username,
                    note_content=note_text
                )
                # Also log note creation to System History for visibility
                PssubfAction.objects.create(
                    task_email_id=f"NOTE_{membership_number}",
                    action_type="Internal Note",
                    action_user=request.user.username,
                    note_content=f"Added profile note: {note_text[:50]}...",
                    action_timestamp=timezone.now()
                )
                messages.success(request, "Internal note added to profile.")
            else:
                messages.warning(request, "Note content cannot be empty.")
            return redirect('beneficiary_details', membership_number=membership_number)

        # --- 3. HANDLE CORE PROFILE UPDATES ---
        # This only runs if the above two specific actions weren't triggered
        else:
            try:
                member.old_membership_number = request.POST.get('old_membership_number')
                member.title = request.POST.get('title')
                member.initials = request.POST.get('initials')
                member.first_name = request.POST.get('first_name')
                member.second_name = request.POST.get('second_name')
                member.last_name = request.POST.get('last_name')
                member.id_number = request.POST.get('id_number')
                member.gender = request.POST.get('gender')
                
                dob_str = request.POST.get('dob')
                if dob_str:
                    dob_date = datetime.strptime(dob_str, '%Y-%m-%d').date()
                    member.dob = dob_date
                    member.cessation_date = dob_date + relativedelta(years=18)
                
                member.employee_number = request.POST.get('employee_number')
                member.stipened_frequency = request.POST.get('stipened_frequency')
                
                stipend_raw = request.POST.get('stipened', '0').replace('R', '').replace(',', '').strip()
                member.stipened = float(stipend_raw) if stipend_raw else 0.00
                
                join_date_str = request.POST.get('fund_join_date')
                if join_date_str:
                    member.fund_join_date = datetime.strptime(join_date_str, '%Y-%m-%d').date()

                member.mobile_1 = request.POST.get('mobile_1')
                member.email_1 = request.POST.get('email_1')
                member.mobile_2 = request.POST.get('mobile_2')
                member.email_2 = request.POST.get('email_2')
                member.mobile_3 = request.POST.get('mobile_3')
                member.email_3 = request.POST.get('email_3')

                member.guardian_title = request.POST.get('guardian_title')
                member.guardian_first_name = request.POST.get('guardian_first_name')
                member.guardian_second_name = request.POST.get('guardian_second_name')
                member.guardian_last_name = request.POST.get('guardian_last_name')
                member.guardian_initial = request.POST.get('guardian_initial')
                member.guardian_mobile = request.POST.get('guardian_mobile')
                member.guardian_email = request.POST.get('guardian_email')
                member.guardian_address = request.POST.get('guardian_address')
                
                member.save()

                PssubfAction.objects.create(
                    task_email_id=f"PROFILE_MOD_{membership_number}",
                    action_type="Profile Update",
                    action_user=request.user.username,
                    note_content="Modified beneficiary personal/financial details.",
                    action_timestamp=timezone.now()
                )

                messages.success(request, f"Changes saved for Member {member.membership_number}.")
                return redirect('beneficiary_details', membership_number=member.membership_number)
                
            except Exception as e:
                messages.error(request, f"Error updating record: {str(e)}")

    # --- 4. FETCH DATA FOR TABS ---
    # (Existing fetch logic continues here...)
    incoming_emails = PssubfDelegate.objects.filter(member_group_code=membership_number)
    outgoing_emails = PssubfDirectEmail.objects.filter(membership_number=membership_number)

    combined_emails = []
    for e in incoming_emails:
        combined_emails.append({
            'agent': e.assigned_agent or "Unassigned",
            'subject': e.subject,
            'date': e.created_at,
            'status': e.status,
            'type': 'INCOMING'
        })

    for e in outgoing_emails:
        combined_emails.append({
            'agent': e.agent_name,
            'subject': e.subject,
            'date': e.sent_at,
            'status': 'Sent',
            'type': 'OUTGOING'
        })

    combined_emails.sort(key=lambda x: x['date'] if x['date'] else timezone.now(), reverse=True)
    internal_notes = PssubfProfileNote.objects.filter(membership_number=membership_number).order_by('-created_at')
    pssubf_actions = PssubfAction.objects.filter(Q(task_email_id__icontains=membership_number)).order_by('-action_timestamp')

    context = {
        'member': member,
        'email_logs': combined_emails,
        'internal_notes': internal_notes,
        'pssubf_actions': pssubf_actions
    }

    return render(request, 'pssubf/beneficiary_details.html', context)

from datetime import date
from django.utils import timezone
from django.http import HttpResponse
import pandas as pd

@login_required
def export_beneficiaries_excel(request):
    """Exports the complete filtered beneficiary list with all columns to Excel."""
    status_filter = request.GET.get('status')
    queryset = PssubfBeneficiary.objects.all().order_by('last_name')

    # Apply same filter logic as the list view
    today = date.today()
    if status_filter == 'expired':
        queryset = queryset.filter(cessation_date__lte=today)
    elif status_filter == 'active':
        queryset = queryset.filter(cessation_date__gt=today)

    # Fetching EVERY column from the schema provided
    data = list(queryset.values(
        'membership_number', 'old_membership_number', 'title', 'initials', 
        'first_name', 'second_name', 'last_name', 'id_number', 'dob', 'gender', 
        'employee_number', 'fund_join_date', 'cessation_date', 
        'stipened_frequency', 'stipened', 
        'mobile_1', 'email_1', 'mobile_2', 'email_2', 'mobile_3', 'email_3',
        'guardian_title', 'guardian_initial', 'guardian_first_name', 
        'guardian_second_name', 'guardian_last_name', 'guardian_dob',
        'guardian_id_number', 'guardian_id_type', 'guardian_gender',
        'guardian_mobile', 'guardian_email', 'guardian_address',
        'created_at', 'updated_at'
    ))

    # Create DataFrame
    df = pd.DataFrame(data)

    # --- FIX FOR TIMEZONE ERROR ---
    # Convert timezone-aware datetimes to naive datetimes
    for col in df.columns:
        if pd.api.types.is_datetime64tz_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)
    
    # Optional: Ensure Decimals are floats for Excel compatibility
    if 'stipened' in df.columns:
        df['stipened'] = df['stipened'].apply(lambda x: float(x) if x is not None else 0.0)

    # Mapping internal field names to readable Excel Headers
    column_mapping = {
        'membership_number': 'Membership Number',
        'old_membership_number': 'Old Membership Number',
        'title': 'Title',
        'initials': 'Initials',
        'first_name': 'First Name',
        'second_name': 'Second Name',
        'last_name': 'Last Name',
        'id_number': 'ID Number',
        'dob': 'Date of Birth',
        'gender': 'Gender',
        'employee_number': 'Employee Number',
        'fund_join_date': 'Fund Join Date',
        'cessation_date': 'Cessation Date',
        'stipened_frequency': 'Stipend Frequency',
        'stipened': 'Stipend Amount',
        'mobile_1': 'Mobile 1',
        'email_1': 'Email 1',
        'mobile_2': 'Mobile 2',
        'email_2': 'Email 2',
        'mobile_3': 'Mobile 3',
        'email_3': 'Email 3',
        'guardian_title': 'Guardian Title',
        'guardian_initial': 'Guardian Initials',
        'guardian_first_name': 'Guardian First Name',
        'guardian_second_name': 'Guardian Second Name',
        'guardian_last_name': 'Guardian Last Name',
        'guardian_dob': 'Guardian DOB',
        'guardian_id_number': 'Guardian ID Number',
        'guardian_id_type': 'Guardian ID Type',
        'guardian_gender': 'Guardian Gender',
        'guardian_mobile': 'Guardian Mobile',
        'guardian_email': 'Guardian Email',
        'guardian_address': 'Guardian Address',
        'created_at': 'Created At',
        'updated_at': 'Updated At'
    }
    
    df.rename(columns=column_mapping, inplace=True)

    # Set up the response as an Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=PSSUBF_Master_Export_{timezone.now().strftime("%Y%m%d_%H%M")}.xlsx'

    # Write the dataframe to the response
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Beneficiaries')
        
        # Access the openpyxl worksheet object to adjust column widths
        worksheet = writer.sheets['Beneficiaries']
        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter # Get the column name
            for cell in col:
                try:
                    if cell.value:
                        val_len = len(str(cell.value))
                        if val_len > max_length:
                            max_length = val_len
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column].width = min(adjusted_width, 50) # Cap width at 50 for readability

    return response