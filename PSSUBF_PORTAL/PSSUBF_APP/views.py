import base64
from datetime import date
from time import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import logging
from django.db.models import Q
import openpyxl
import pandas as pd
from django.db import transaction
from dateutil.relativedelta import relativedelta
from django.core.paginator import Paginator
from datetime import datetime
from .services.outlook_graph_service import OutlookGraphService

logger = logging.getLogger(__name__)

# Import your unmanaged models
from .models import AdHocList, ClaimAffordability, ClaimList, PssubfBeneficiary, PssubfDirectEmail, PssubfInbox, PssubfDelegate, PssubfAction, PssubfNote, PssubfProfileNote
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

from django.db.models import Q

@login_required
def pssubf_dashboard(request):
    """
    Shows all emails that haven't been processed yet.
    Excludes emails with 'Delegated' or 'Completed' status.
    """
    # We exclude specific statuses. This ensures that 'New', NULL, 
    # or empty statuses still show up in your triage list.
    inbox_items = PssubfInbox.objects.exclude(
        Q(status__iexact='Delegated') | 
        Q(status__iexact='Completed')
    ).order_by('-received_timestamp')

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
    Now includes Call Audit fields (Direction, Method, Type).
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

        # 2. Add Internal Note (Updated with Call Audit)
        elif action_type == 'add_note':
            note_text = request.POST.get('note_content')
            new_category = request.POST.get('email_category')
            new_status = request.POST.get('status')
            
            # Capture New Call Fields
            call_direction = request.POST.get('call_direction', 'Outbound')
            call_method = request.POST.get('call_method', 'Note')
            call_type = request.POST.get('call_type', 'General Note')
            
            if new_category:
                task.email_category = new_category
            if new_status:
                task.status = new_status
            task.save()

            # Save to pssubf_notes (Added audit fields to text for now, 
            # or update your model fields if you added specific columns)
            audit_string = f"[{call_direction} | {call_method} | {call_type}]"
            
            PssubfNote.objects.create(
                task_email_id=email_id,
                agent_name=request.user.username,
                note_text=f"{audit_string} {note_text}",
                classification_at_time=task.email_category,
                status_at_time=task.status
            )

            # Save to pssubf_actions
            PssubfAction.objects.create(
                task_email_id=email_id,
                action_user=request.user.username,
                action_type="NOTE",
                note_content=f"{audit_string} {note_text}"
            )
            messages.success(request, "Internal note saved.")

        # 3. Handle External Email Reply (Updated with Call Audit)
        elif action_type == 'send_reply':
            recipient = request.POST.get('reply_recipient')
            subject = request.POST.get('reply_subject')
            body_content = request.POST.get('reply_body')
            
            # Fixed values for Email Reply audit
            call_direction = "Outbound"
            call_method = "Emails"
            call_type = "Feedback to Beneficiary"

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

            # Send via Outlook
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
                audit_string = f"[{call_direction} | {call_method} | {call_type}]"
                
                # LOGGING: Save to pssubf_actions
                PssubfAction.objects.create(
                    task_email_id=email_id,
                    action_user=request.user.username,
                    action_type="EMAIL_REPLY",
                    note_content=f"{audit_string}\nTo: {recipient}\nSubject: {subject}\n\n{body_content}"
                )

                # LOGGING: Save to pssubf_notes
                PssubfNote.objects.create(
                    task_email_id=email_id,
                    agent_name=request.user.username,
                    note_text=f"{audit_string} REPLY SENT TO {recipient}: {body_content}",
                    classification_at_time=task.email_category,
                    status_at_time=task.status
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

    # --- GET Logic ---
    email_data = OutlookGraphService._make_graph_request(f"messages/{email_id}", method='GET')
    attachments = OutlookGraphService.fetch_attachments(target_email, email_id)
    email_content = email_data.get('body', {}).get('content', 'Content unavailable.')

    # Inline Image Resolution
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

    # Fetch History
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
    Displays the active queue, excluding completed and recycled items.
    """
    # Exclude both Recycled and Completed to keep the dashboard focused on active work
    delegations = PssubfDelegate.objects.exclude(
        status__in=['Recycled', 'Completed', 'Complete']
    ).order_by('-created_at')
    
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
    # 1. Get all records from the database
    queryset = PssubfBeneficiary.objects.all().order_by('last_name')

    # 2. Filter Logic (Status based on cessation_date)
    status_filter = request.GET.get('status')
    today = date.today()  # Live date for current calculation

    if status_filter == 'expired':
        # Members 18 and older (cessation date has passed or is today)
        queryset = queryset.filter(cessation_date__lte=today)
    elif status_filter == 'active':
        # Members under 18 (cessation date is in the future)
        queryset = queryset.filter(cessation_date__gt=today)

    # 3. Pagination (36 records per page)
    paginator = Paginator(queryset, 36)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 4. LIVE CALCULATION: Years and Months
    # This loop runs only for the 36 records on the current page for performance
    for member in page_obj:
        if member.dob:
            birth = member.dob
            
            # Calculate total months difference
            # Formula: (Years Diff * 12) + Months Diff
            total_months = (today.year - birth.year) * 12 + (today.month - birth.month)
            
            # Adjustment: If today's day of the month is earlier than the birth day, 
            # the current month hasn't fully completed yet.
            if today.day < birth.day:
                total_months -= 1
            
            # Prevent negative months for edge cases
            total_months = max(0, total_months)
            
            # Split total months into Years (Y) and remaining Months (M)
            years = total_months // 12
            months = total_months % 12
            
            # Format output: e.g., "19Y 03M"
            # Using :02d ensures months always show two digits (e.g., 03M instead of 3M)
            member.calculated_age = f"{years}Y {months:02d}M"
        else:
            member.calculated_age = "N/A"

    # 5. Handle Session Errors (from Excel imports)
    import_errors = request.session.pop('import_errors', [])
    
    return render(request, 'pssubf/beneficiary_list.html', {
        'page_obj': page_obj,
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
        elif 'save_note' in request.POST:
            note_text = request.POST.get('note_text')
            if note_text:
                current_status = "Expired" if member.is_expired else "Active"
                PssubfNote.objects.create(
                    task_email_id=f"PROFILE_{membership_number}",
                    agent_name=request.user.username,
                    note_text=note_text,
                    classification_at_time="Profile Detail Note",
                    status_at_time=current_status
                )
                PssubfProfileNote.objects.create(
                    membership_number=membership_number,
                    agent_name=request.user.username,
                    note_content=note_text
                )
                PssubfAction.objects.create(
                    task_email_id=f"NOTE_{membership_number}",
                    action_type="Internal Note",
                    action_user=request.user.username,
                    note_content=f"Added profile note: {note_text[:50]}...",
                    action_timestamp=timezone.now()
                )
                messages.success(request, "Internal note added to profile.")
            return redirect('beneficiary_details', membership_number=membership_number)

        # --- 3. HANDLE CORE PROFILE UPDATES ---
        else:
            try:
                # ... (Profile update logic remains the same as your previous version)
                member.old_membership_number = request.POST.get('old_membership_number')
                member.title = request.POST.get('title')
                member.initials = request.POST.get('initials')
                member.first_name = request.POST.get('first_name')
                member.second_name = request.POST.get('second_name')
                member.last_name = request.POST.get('last_name')
                member.id_number = request.POST.get('id_number')
                
                dob_str = request.POST.get('dob')
                if dob_str:
                    dob_date = datetime.strptime(dob_str, '%Y-%m-%d').date()
                    member.dob = dob_date
                    member.cessation_date = dob_date + relativedelta(years=18)
                
                member.employee_number = request.POST.get('employee_number')
                member.stipened_frequency = request.POST.get('stipened_frequency')
                
                stipend_raw = str(request.POST.get('stipened', '0')).replace('R', '').replace(',', '').strip()
                member.stipened = float(stipend_raw) if stipend_raw else 0.00
                
                join_date_str = request.POST.get('fund_join_date')
                if join_date_str:
                    member.fund_join_date = datetime.strptime(join_date_str, '%Y-%m-%d').date()

                member.mobile_1 = request.POST.get('mobile_1')
                member.email_1 = request.POST.get('email_1')
                member.mobile_2 = request.POST.get('mobile_2')
                member.email_2 = request.POST.get('email_2')

                member.guardian_title = request.POST.get('guardian_title')
                member.guardian_first_name = request.POST.get('guardian_first_name')
                member.guardian_last_name = request.POST.get('guardian_last_name')
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
    claims = ClaimList.objects.filter(beneficiary=member).order_by('-date_logged')
    adhoc_records = AdHocList.objects.filter(beneficiary=member).order_by('-claim_form_date')

    incoming_emails = PssubfDelegate.objects.filter(member_group_code=membership_number)
    outgoing_emails = PssubfDirectEmail.objects.filter(membership_number=membership_number)

    combined_emails = []
    for e in incoming_emails:
        combined_emails.append({
            'email_id': e.email_id, 
            'agent': e.assigned_agent or "Unassigned",
            'subject': e.subject,
            'date': e.created_at,
            'status': e.status,
            'type': 'INCOMING'
        })

    for e in outgoing_emails:
        combined_emails.append({
            # We prefix local IDs to differentiate them from Graph API IDs in the URL
            'email_id': f"DIRECT_{e.id}", 
            'agent': e.agent_name,
            'subject': e.subject,
            'date': e.sent_at,
            'status': 'Sent',
            'type': 'OUTGOING'
        })

    combined_emails.sort(key=lambda x: x['date'] if x['date'] else timezone.now(), reverse=True)
    
    internal_notes = PssubfNote.objects.filter(task_email_id__icontains=membership_number).order_by('-created_at')
    pssubf_actions = PssubfAction.objects.filter(Q(task_email_id__icontains=membership_number)).order_by('-action_timestamp')

    context = {
        'member': member,
        'claims': claims,
        'adhoc_records': adhoc_records,
        'email_logs': combined_emails,
        'internal_notes': internal_notes,
        'pssubf_actions': pssubf_actions,
        'title': f"Member Profile - {membership_number}"
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

@login_required
def get_beneficiary_data(request, membership_number):
    """API endpoint to auto-populate the New Claim popup"""
    member = get_object_or_404(PssubfBeneficiary, membership_number=membership_number)
    
    # Calculate age for the age_at_claim field (initial calculation)
    today = timezone.now().date()
    age = today.year - member.dob.year - ((today.month, today.day) < (member.dob.month, member.dob.day))
    
    data = {
        'guardian_name': f"{member.guardian_first_name or ''} {member.guardian_last_name or ''}".strip(),
        'beneficiary_name': f"{member.first_name} {member.last_name}",
        'dob': member.dob.strftime('%Y-%m-%d'),
        'termination_date': member.cessation_date.strftime('%Y-%m-%d') if member.cessation_date else '',
        'stipened': float(member.stipened or 0),
        'age': age
    }
    return JsonResponse(data)

@login_required
def claim_list_view(request):
    """Main view for the full Claim Registry with Agent Tracking and File Management"""
    
    def clean_numeric(val):
        if not val: return 0
        return str(val).replace('R', '').replace(',', '').replace('%', '').strip()

    if request.method == 'POST':
        action = request.POST.get('action')
        m_num = request.POST.get('membership_number')
        
        try:
            # We use .filter().first() instead of get_object_or_404 
            # so the system doesn't crash if adding a claim for a non-existent member
            member = PssubfBeneficiary.objects.filter(membership_number=m_num).first()
            uploaded_file = request.FILES.get('supporting_document')
            file_name = uploaded_file.name if uploaded_file else None

            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
            agent_stamp = f"\n\n--- Managed by {request.user.username} on {timestamp} ---"

            if action == 'add_claim_entry':
                ClaimList.objects.create(
                    beneficiary=member, # Can be None for imported/historical lines
                    beneficiary_membership_number=m_num, # Ensure raw field is saved
                    reference_no=f"CLM-{timezone.now().strftime('%Y%m%d%H%M')}",
                    guardian_name=request.POST.get('guardian_name'),
                    beneficiary_name=request.POST.get('beneficiary_name'),
                    beneficiary_dob=request.POST.get('beneficiary_dob') or None,
                    termination_date=request.POST.get('termination_date') or None,
                    claim_type=request.POST.get('claim_type'),
                    description=(request.POST.get('description') or "") + agent_stamp,
                    date_logged=request.POST.get('date_logged') or None,
                    status=request.POST.get('status', 'Created'),
                    portfolio_value=clean_numeric(request.POST.get('portfolio_value')),
                    portfolio_date=request.POST.get('portfolio_date') or None,
                    amount_requested=clean_numeric(request.POST.get('amount_requested')),
                    age_at_claim=request.POST.get('age_at_claim'),
                    supporting_docs_attached=request.POST.get('supporting_docs_attached'),
                    monthly_income_payment=clean_numeric(request.POST.get('monthly_income')),
                    date_paid=request.POST.get('date_paid') or None,
                    loaded_by_agent=request.user.username,
                    attachment_path=file_name
                )
                msg = f"Claim for Member {m_num} logged."

            elif action == 'update_claim_entry':
                claim_id = request.POST.get('claim_id')
                claim = get_object_or_404(ClaimList, id=claim_id)
                
                if file_name:
                    claim.attachment_path = file_name
                elif request.POST.get('remove_attachment') == 'true':
                    claim.attachment_path = None

                claim.guardian_name = request.POST.get('guardian_name')
                claim.beneficiary_name = request.POST.get('beneficiary_name')
                claim.beneficiary_dob = request.POST.get('beneficiary_dob') or None
                claim.termination_date = request.POST.get('termination_date') or None
                claim.date_paid = request.POST.get('date_paid') or None
                claim.claim_type = request.POST.get('claim_type')
                claim.description = (request.POST.get('description') or "") + agent_stamp
                claim.date_logged = request.POST.get('date_logged') or None
                claim.status = request.POST.get('status')
                claim.portfolio_value = clean_numeric(request.POST.get('portfolio_value'))
                claim.portfolio_date = request.POST.get('portfolio_date') or None
                claim.amount_requested = clean_numeric(request.POST.get('amount_requested'))
                claim.age_at_claim = request.POST.get('age_at_claim')
                claim.supporting_docs_attached = request.POST.get('supporting_docs_attached')
                claim.monthly_income_payment = clean_numeric(request.POST.get('monthly_income'))
                
                claim.save()
                msg = f"Claim {claim_id} updated."

            PssubfAction.objects.create(
                task_email_id=f"CLAIM_{m_num}",
                action_type="Claim Record Managed",
                action_user=request.user.username,
                note_content=f"Action: {action} | Status: {request.POST.get('status')}",
                action_timestamp=timezone.now()
            )
            
            messages.success(request, msg)
            return redirect('claim_list')
            
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    # FETCH LOGIC: 
    # Removed select_related('beneficiary') to ensure we get ALL claims, 
    # even those without a matching member profile.
    membership_number = request.GET.get('membership_number')
    claims = ClaimList.objects.all().order_by('-date_logged')
    
    if membership_number:
        claims = claims.filter(beneficiary_membership_number=membership_number)

    return render(request, 'claim_list.html', {'claims': claims, 'title': 'Claims Registry'})

@login_required
def ad_hoc_list_view(request):
    """
    Main view for the Ad Hoc Registry handling Saves, Updates, 
    and calculation storage with Agent Tracking.
    """
    
    if request.method == 'POST':
        action = request.POST.get('action')
        m_num = request.POST.get('membership_number')
        
        try:
            # Fetch the beneficiary based on membership number
            member = get_object_or_404(PssubfBeneficiary, membership_number=m_num)
            uploaded_file = request.FILES.get('supporting_document')
            file_name = uploaded_file.name if uploaded_file else None

            # Agent Tracking Logic: Creates a signature stamp for the claim note
            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
            agent_stamp = f"\n\n--- Managed by {request.user.username} on {timestamp} ---"

            # Helper function to clean numeric/percentage inputs from UI for DB storage
            def clean_decimal(value):
                if not value or value == '': return 0.00
                return str(value).replace('%', '').strip()

            if action == 'add_adhoc_entry':
                AdHocList.objects.create(
                    beneficiary=member,
                    title=request.POST.get('title'), # UI: Reason
                    comments=(request.POST.get('comments') or "") + agent_stamp,
                    claim_form_date=request.POST.get('claim_form_date') or None,
                    date_paid=request.POST.get('date_paid') or None,
                    status=request.POST.get('status', 'Created'),
                    supporting_docs_attached=request.POST.get('supporting_docs_attached', 'No'),
                    attachment_path=file_name,
                    # Financial fields and calculations
                    portfolio_value=clean_decimal(request.POST.get('portfolio_value')),
                    portfolio_date=request.POST.get('portfolio_date') or None,
                    amount_requested=clean_decimal(request.POST.get('amount_requested')),
                    years_to_maturity=request.POST.get('years_to_maturity') or 0,
                    affordability_calculation=request.POST.get('affordability_calculation') # Saved as string "X.XX%"
                )
                messages.success(request, f"New Ad Hoc claim for Member {m_num} successfully logged.")

            elif action == 'update_adhoc_entry':
                record_id = request.POST.get('record_id')
                record = get_object_or_404(AdHocList, id=record_id)
                
                # File Management: Update only if a new file is uploaded or removal requested
                if file_name:
                    record.attachment_path = file_name
                elif request.POST.get('remove_attachment') == 'true':
                    record.attachment_path = None

                # Update core metadata
                record.title = request.POST.get('title')
                record.status = request.POST.get('status')
                record.claim_form_date = request.POST.get('claim_form_date') or None
                record.date_paid = request.POST.get('date_paid') or None
                record.supporting_docs_attached = request.POST.get('supporting_docs_attached')
                
                # Update financial values and calculations
                record.portfolio_value = clean_decimal(request.POST.get('portfolio_value'))
                record.portfolio_date = request.POST.get('portfolio_date') or None
                record.amount_requested = clean_decimal(request.POST.get('amount_requested'))
                record.years_to_maturity = request.POST.get('years_to_maturity') or 0
                record.affordability_calculation = request.POST.get('affordability_calculation')

                # Maintain Agent Tracking history in the Claim Note
                user_comments = request.POST.get('comments') or ""
                if agent_stamp not in (record.comments or ""):
                    record.comments = user_comments + agent_stamp
                else:
                    record.comments = user_comments

                record.save()
                messages.success(request, f"Ad Hoc Record {record_id} has been updated.")

            return redirect('adhoc_list')
            
        except Exception as e:
            messages.error(request, f"Process Error: {str(e)}")

    # GET logic: Populate registry table with filtering support
    membership_number = request.GET.get('membership_number')
    # Use select_related to optimize the join with the Beneficiary table
    adhoc_records = AdHocList.objects.all().select_related('beneficiary').order_by('-date_created')

    if membership_number:
        adhoc_records = adhoc_records.filter(beneficiary__membership_number=membership_number)

    context = {
        'adhoc_list': adhoc_records,
        'title': 'Ad Hoc Registry'
    }
    return render(request, 'Ad_hoc_list.html', context)

@login_required
def get_claim_details(request, claim_id):
    """Fetches full claim data and cleans the description for editing"""
    claim = get_object_or_404(ClaimList, id=claim_id)
    member = claim.beneficiary
    
    # Clean the description so the agent doesn't edit the old tracking stamps
    clean_description = claim.description or ""
    if "--- Managed by" in clean_description:
        clean_description = clean_description.split("---")[0].strip()

    data = {
        'membership_number': member.membership_number,
        'guardian_name': f"{member.guardian_first_name or ''} {member.guardian_last_name or ''}".strip(),
        'beneficiary_name': f"{member.first_name} {member.last_name}",
        'dob': member.dob.strftime('%Y-%m-%d') if member.dob else '',
        'term_date': member.cessation_date.strftime('%Y-%m-%d') if member.cessation_date else '',
        
        'claim_type': claim.claim_type,
        'age_at_claim': claim.age_at_claim,
        'monthly_income': float(claim.monthly_income_payment or 0),
        'date_logged': claim.date_logged.strftime('%Y-%m-%d') if claim.date_logged else '',
        'portfolio_value': float(claim.portfolio_value or 0),
        'portfolio_date': claim.portfolio_date.strftime('%Y-%m-%d') if claim.portfolio_date else '',
        'amount_requested': float(claim.amount_requested or 0),
        'status': claim.status,
        'date_paid': claim.date_paid.strftime('%Y-%m-%d') if hasattr(claim, 'date_paid') and claim.date_paid else '',
        'description': clean_description,
        'docs_attached': claim.supporting_docs_attached
    }
    return JsonResponse(data)

@login_required
def get_adhoc_details(request, record_id):
    """
    AJAX helper to populate the Edit Modal. 
    Sourced directly from both the AdHoc record and the related Beneficiary table.
    """
    record = get_object_or_404(AdHocList, id=record_id)
    member = record.beneficiary
    
    # 1. Parse Tracking Information for the Modal Footer
    tracking_info = ""
    if record.comments and "--- Managed by" in record.comments:
        # Extracts the last agent stamp for display in the footer
        tracking_info = record.comments.split("---")[-1].replace("---", "").strip()

    # 2. Clean the Note for the Textarea
    # We remove the system stamps so the agent only sees the actual notes they wrote
    display_comments = record.comments or ""
    if "--- Managed by" in display_comments:
        display_comments = display_comments.split("---")[0].strip()

    # 3. Construct JSON response
    data = {
        # Beneficiary specific fields (Read-Only in UI)
        'membership_number': member.membership_number,
        'beneficiary_name': f"{member.first_name} {member.last_name}",
        'guardian_name': f"{member.guardian_first_name} {member.guardian_last_name}",
        'id_number': member.id_number or "N/A",
        'dob': member.dob.strftime('%Y-%m-%d') if member.dob else '',
        'termination_date': member.cessation_date.strftime('%Y-%m-%d') if member.cessation_date else '',
        'stipened': f"R {member.monthly_stipened or 0.00}",
        
        # AdHoc Claim specific fields
        'title': record.title, # Reason
        'status': record.status,
        'claim_form_date': record.claim_form_date.strftime('%Y-%m-%d') if record.claim_form_date else '',
        'date_paid': record.date_paid.strftime('%Y-%m-%d') if record.date_paid else '',
        
        # Financials & Calculations
        'portfolio_value': float(record.portfolio_value or 0),
        'portfolio_date': record.portfolio_date.strftime('%Y-%m-%d') if record.portfolio_date else '',
        'amount_requested': float(record.amount_requested or 0),
        'years_to_maturity': record.years_to_maturity or 0,
        'affordability_calculation': record.affordability_calculation or '0.00%',
        
        # Metadata & Tracking
        'docs_attached': record.supporting_docs_attached,
        'comments': display_comments, # Cleaned note for editing
        'attachment_path': record.attachment_path or '',
        'tracking_info': f"Last activity: {tracking_info}" if tracking_info else "No recent agent activity recorded"
    }
    
    return JsonResponse(data)

from openpyxl.styles import Font, PatternFill, Alignment
@login_required
def export_adhoc_excel(request):
    """
    Exports the Ad Hoc Registry to Excel with columns A through R.
    Calculates age at time of claim and parses agent tracking.
    """
    # Create workbook and worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ad Hoc Claims"

    # Define the headers exactly as requested (A to R)
    headers = [
        'Member Number', 'Guardian Name & Surname', 'Beneficiary Name & Surname', 
        'Beneficiary Date Of Birth', 'Age at Claim Date', 'Termination Date', 
        'Years to Maturity', 'Original Claim Form Date', 'Portfolio Value', 
        'Portfolio Value Date', 'Monthly Income Payment', 'Amount Requested', 
        'Reason', 'Supporting Documents Attached', 'Affordability Calc', 
        'Note', 'Date Paid', 'Loaded by Agent'
    ]
    ws.append(headers)

    # Styling headers: Futura Green background with Bold White text
    header_fill = PatternFill(start_color="8FCE7F", end_color="8FCE7F", fill_type="solid")
    header_font = Font(bold=True, color="000000")
    
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # Get records with select_related to optimize database performance
    records = AdHocList.objects.all().select_related('beneficiary').order_by('-date_created')

    for rec in records:
        # 1. Calculate Age at Claim Date (Column E)
        age_display = ""
        if rec.beneficiary.dob and rec.claim_form_date:
            dob = rec.beneficiary.dob
            cfd = rec.claim_form_date
            # Precise age calculation at the moment of claim
            age = cfd.year - dob.year - ((cfd.month, cfd.day) < (dob.month, dob.day))
            age_display = str(age)

        # 2. Extract "Loaded by Agent" (Column R)
        agent_info = "System"
        if rec.comments and "Managed by" in rec.comments:
            try:
                # Parses the name between "Managed by" and "on"
                agent_info = rec.comments.split("Managed by")[-1].split("on")[0].strip()
            except (IndexError, ValueError):
                agent_info = "Unknown"

        # 3. Clean Note (Column P)
        # Strips away the system agent stamps for the spreadsheet
        clean_note = rec.comments.split("---")[0].strip() if rec.comments else ""

        # 4. Append row data (A to R)
        ws.append([
            rec.beneficiary.membership_number,                       # A
            f"{rec.beneficiary.guardian_first_name} {rec.beneficiary.guardian_last_name}", # B
            f"{rec.beneficiary.first_name} {rec.beneficiary.last_name}", # C
            rec.beneficiary.dob.strftime('%Y-%m-%d') if rec.beneficiary.dob else "", # D
            age_display,                                              # E
            rec.beneficiary.cessation_date.strftime('%Y-%m-%d') if rec.beneficiary.cessation_date else "", # F
            rec.years_to_maturity,                                    # G
            rec.claim_form_date.strftime('%Y-%m-%d') if rec.claim_form_date else "", # H
            rec.portfolio_value,                                      # I
            rec.portfolio_date.strftime('%Y-%m-%d') if rec.portfolio_date else "", # J
            rec.beneficiary.monthly_stipened,                         # K
            rec.amount_requested,                                     # L
            rec.title,                                                # M
            rec.supporting_docs_attached,                             # N
            rec.affordability_calculation,                            # O
            clean_note,                                               # P
            rec.date_paid.strftime('%Y-%m-%d') if rec.date_paid else "", # Q
            agent_info                                                # R
        ])

    # 5. Auto-adjust column widths for better readability
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width

    # Generate Response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=AdHoc_Export_{date.today()}.xlsx'
    wb.save(response)
    
    return response

@login_required
def export_claims_excel(request):
    """
    Exports the Claim Registry (ClaimList model) to Excel.
    Sequence: A-Member Number to M-Supporting Docs.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Claims Registry Export"

    # Define exact header mapping A-M + specific metadata
    headers = [
        'Member Number',                # A
        'Guardian Name & Surname',      # B
        'Beneficiary Name & Surname',   # C
        'Beneficiary Date Of Birth',    # D
        'Age at Claim Date',            # E
        'Termination Date',             # F
        'Original Claim Form Date',     # G
        'Portfolio Value',              # H
        'Portfolio Value Date',         # I
        'Monthly Income Payment',       # J
        'Amount Requested',             # K
        'Reason',                       # L
        'Date Paid',                    
        'Loaded by Agent',              
        'Supporting Documents Attached' # M
    ]
    ws.append(headers)

    # Styling for Green Registry Theme
    header_fill = PatternFill(start_color="059669", end_color="059669", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill

    # Get records with select_related to pull Beneficiary data efficiently
    records = ClaimList.objects.all().select_related('beneficiary').order_by('-date_logged')

    for rec in records:
        # Age Calculation for Column E: Claim Date (date_logged) vs Beneficiary DOB
        age_display = ""
        if rec.beneficiary.dob and rec.date_logged:
            dob = rec.beneficiary.dob
            dl = rec.date_logged
            age = dl.year - dob.year - ((dl.month, dl.day) < (dob.month, dob.day))
            age_display = str(age)

        # Agent Extraction logic from Description stamp
        agent_info = "N/A"
        if rec.description and "Managed by" in rec.description:
            try:
                agent_info = rec.description.split("Managed by")[-1].split("on")[0].strip()
            except:
                pass

        ws.append([
            rec.beneficiary.membership_number,                       # A
            f"{rec.beneficiary.guardian_first_name} {rec.beneficiary.guardian_last_name}", # B
            f"{rec.beneficiary.first_name} {rec.beneficiary.last_name}", # C
            rec.beneficiary.dob.strftime('%Y-%m-%d') if rec.beneficiary.dob else "", # D
            age_display,                                              # E
            rec.beneficiary.cessation_date.strftime('%Y-%m-%d') if rec.beneficiary.cessation_date else "", # F
            rec.date_logged.strftime('%Y-%m-%d') if rec.date_logged else "", # G (Original Claim Form Date)
            rec.portfolio_value,                                      # H
            rec.portfolio_date.strftime('%Y-%m-%d') if rec.portfolio_date else "", # I
            rec.monthly_income_payment,                               # J
            rec.amount_requested,                                     # K
            rec.claim_type,                                           # L (Reason)
            rec.date_paid.strftime('%Y-%m-%d') if hasattr(rec, 'date_paid') and rec.date_paid else "", # Date Paid
            agent_info,                                               # Loaded by Agent
            rec.supporting_docs_attached                              # M
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Claims_List_{date.today()}.xlsx'
    wb.save(response)
    return response

from dateutil.relativedelta import relativedelta

@login_required
def affordability_dashboard(request):
    """View the calculator and history"""
    results = ClaimAffordability.objects.all().order_by('-calculated_at')
    return render(request, 'affordability_dashboard.html', {'results': results})

@login_required
def run_manual_calc(request):
    """Pulls data from Beneficiaries table and calculates affordability"""
    if request.method == 'POST':
        m_num = request.POST.get('membership_number')
        
        # 1. Pull data from the Beneficiaries Table
        member = get_object_or_404(PssubfBeneficiary, membership_number=m_num)
        
        # 2. Get User Inputs
        fund_val = float(request.POST.get('fund_value') or 0)
        quote_amt = float(request.POST.get('quote_amount') or 0)
        
        # Use Beneficiary data for the rest
        dob = member.dob
        stipend = float(member.stipened or 0) # Pulls 'stipened' from your column list
        
        if dob:
            # 3. Excel Logic (Months to 18)
            majority_date = dob + relativedelta(years=18)
            diff = relativedelta(majority_date, date.today())
            total_months = (diff.years * 12) + diff.months
            years_to_maj = round(total_months / 12, 2)

            # 4. Financial Projection
            total_stipend_cost = stipend * total_months
            fund_after_stipend = fund_val - total_stipend_cost
            final_bal = fund_after_stipend - quote_amt

            # 5. Save to Analysis Table
            ClaimAffordability.objects.update_or_create(
                membership_number=m_num,
                defaults={
                    'majority_date': majority_date,
                    'years_to_majority': years_to_maj,
                    'months_to_majority': total_months,
                    'total_stipend_commitment': total_stipend_cost,
                    'fund_after_stipend': fund_after_stipend,
                    'final_projected_balance': final_bal,
                    'requires_letter': final_bal < 0
                }
            )
            
    return redirect('affordability_dashboard')

import io
from django.http import HttpResponse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

@login_required
def download_email_eml(request, email_id):
    """
    Generates and downloads a .eml file for both Delegated and Direct emails.
    """
    msg = MIMEMultipart()
    
    if email_id.startswith("DIRECT_"):
        # Fetch from local Direct Email table
        local_id = email_id.replace("DIRECT_", "")
        email_obj = get_object_or_404(PssubfDirectEmail, id=local_id)
        
        msg['Subject'] = email_obj.subject
        msg['From'] = settings.OUTLOOK_EMAIL_ADDRESS
        msg['To'] = email_obj.recipient
        body_content = email_obj.body_html
    else:
        # Fetch from Delegated incoming table
        task = get_object_or_404(PssubfDelegate, email_id=email_id)
        msg['Subject'] = task.subject or "(No Subject)"
        msg['From'] = task.sender or "System"
        msg['To'] = settings.OUTLOOK_EMAIL_ADDRESS
        body_content = f"Source: PSSUBF Portal Delegation\nSender: {task.sender}\nDate: {task.created_at}"

    msg.attach(MIMEText(body_content, 'html'))

    buf = io.BytesIO()
    buf.write(msg.as_bytes())
    buf.seek(0)
    
    response = HttpResponse(buf.read(), content_type='message/rfc822')
    response['Content-Disposition'] = f'attachment; filename="Email_Record.eml"'
    return response