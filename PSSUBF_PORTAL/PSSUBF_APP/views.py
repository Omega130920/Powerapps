import base64
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import logging
from django.db.models import Q
logger = logging.getLogger(__name__)

# Import your unmanaged models
from .models import PssubfInbox, PssubfDelegate, PssubfAction
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
    """Hybrid Dashboard: Fetches live data and filters against local status."""
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    
    # Call the newly added method
    inbox_data = OutlookGraphService.fetch_inbox_messages(top_count=50) 
    
    if 'error' in inbox_data:
        messages.error(request, f"Graph Error: {inbox_data['error']}")
        return render(request, 'pssubf/inbox_list.html', {'messages': []})

    all_emails = inbox_data.get('value', [])
    email_ids = [e['id'] for e in all_emails]
    
    # Filter out anything already delegated (using PssubfDelegate table)
    delegated_ids = PssubfDelegate.objects.filter(
        email_id__in=email_ids
    ).exclude(status='Pending').values_list('email_id', flat=True)

    filtered_emails = []
    for email in all_emails:
        if email['id'] in delegated_ids:
            continue
        filtered_emails.append(email)

    return render(request, 'pssubf/inbox_list.html', {
        'messages': filtered_emails, 
        'target_email': target_email
    })

@login_required
def pssubf_delegate_view(request, email_id):
    """View to fetch live email details, resolve inline images, and delegate to an agent."""
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    # Fetch local record if it exists for fallback
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
        
        # 🚀 FIX: Resolve Inline Images (Signatures, etc.)
        for att in attachments:
            # Handle inline images specifically for the email body
            if att.get('isInline') and att.get('contentId'):
                cid = att.get('contentId')
                raw = OutlookGraphService.get_attachment_raw(target_email, email_id, att['id'])
                if raw and isinstance(raw, dict) and 'contentBytes' in raw:
                    base64_data = raw['contentBytes']
                    content_type = att.get('contentType', 'image/png')
                    
                    # Replace CID link with Base64 Data URI
                    data_url = f"data:{content_type};base64,{base64_data}"
                    email_content = email_content.replace(f"cid:{cid}", data_url)
                    
                    # Attach bytes to object for potential gallery use
                    att['contentBytes'] = base64_data
            
            # Handle standard image attachments (thumbnails)
            elif 'image' in att.get('contentType', '').lower() and not att.get('contentBytes'):
                raw = OutlookGraphService.get_attachment_raw(target_email, email_id, att['id'])
                if raw and isinstance(raw, dict) and 'contentBytes' in raw:
                    att['contentBytes'] = raw['contentBytes']

    return render(request, 'pssubf/delegate.html', {
        'email_id': email_id,
        'email_subject': email_subject,
        'email_content': email_content,
        'attachments': attachments,
        'available_users': available_users,
        'inbox_item': inbox_item
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

        # 2. Add Internal Note
        elif action_type == 'add_note':
            note_text = request.POST.get('note_content')
            PssubfAction.objects.create(
                task_email_id=email_id,
                action_user=request.user.username,
                action_type="NOTE",
                note_content=note_text
            )
            messages.success(request, "Internal note saved.")

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

    # 🚀 FIX: Resolve Inline Images (Signatures, etc.)
    for att in attachments:
        # Check if it's an inline attachment with a Content-ID
        if att.get('isInline') and att.get('contentId'):
            cid = att.get('contentId')
            # Fetch the raw bytes if not already included
            raw = OutlookGraphService.get_attachment_raw(target_email, email_id, att['id'])
            if raw and isinstance(raw, dict) and 'contentBytes' in raw:
                base64_data = raw['contentBytes']
                content_type = att.get('contentType', 'image/png')
                
                # Replace the CID link with a Base64 Data URL
                data_url = f"data:{content_type};base64,{base64_data}"
                email_content = email_content.replace(f"cid:{cid}", data_url)
                
                # Also store it in the attachment object for the gallery/list view
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