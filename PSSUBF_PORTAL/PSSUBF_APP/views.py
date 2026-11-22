import base64
import csv
from datetime import date, datetime
from email import parser
import random
import re
import traceback
from dateutil import parser as date_parser
from django.utils import timezone  # Ensured django timezone is used
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, HttpResponse, Http404, JsonResponse, StreamingHttpResponse, request
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import logging
from django.db.models import Q
import openpyxl
import pandas as pd
from django.db import transaction
from dateutil.relativedelta import relativedelta
from django.core.paginator import Paginator
from .services.outlook_graph_service import OutlookGraphService
from urllib.parse import unquote, quote

logger = logging.getLogger(__name__)

# Import your unmanaged models
from .models import AdHocList, ClaimAffordability, ClaimHistory, ClaimList, PssubfBeneficiary, PssubfDirectEmail, PssubfInbox, PssubfDelegate, PssubfAction, PssubfNote, PssubfProfileNote, SmsLog
# Import your verified services
from PSSUBF_APP.services.outlook_graph_service import OutlookGraphService
from PSSUBF_APP.services.delegation_service import delegate_pssubf_task


# --- HELPER FUNCTION: Safely formats plain text to HTML paragraphs ---
def format_email_body(text):
    if not text:
        return ""
    # If the text already contains HTML tags (like from a rich text editor), leave it alone.
    if '<p>' in text.lower() or '<br' in text.lower():
        return text
    # Otherwise, convert plain text line breaks into HTML breaks
    return text.replace('\r\n', '<br>').replace('\n', '<br>')

def clean_numeric(val):
    if not val or str(val).lower() == 'undefined' or str(val).strip() == '': 
        return 0
    return str(val).replace('R', '').replace(',', '').replace('%', '').strip()

@login_required
def pssubf_switchboard(request):
    """
    Main Menu / Switchboard.
    Mapped to path('')
    Renders the card-based navigation (dashboard.html).
    """
    
    # 🟢 Explicitly pass user context to ensure names display correctly
    context = {
        'user': request.user,
    }
    
    return render(request, 'pssubf/dashboard.html', context)

from .models import SystemLog

# Regex matching: [Inbound | Emails | New Claim Pack Received (Complete)] Complete claim received
BRACKETED_LOG_PATTERN = re.compile(
    r'^\s*\[\s*([^|\]]+?)\s*\|\s*([^|\]]+?)\s*\|\s*([^\]]+?)\s*\]\s*(.*)$',
    re.DOTALL
)


def _infer_log_category(call_type, existing_classification=None):
    """Determines the SystemLog category from existing classification or call_type keywords."""
    valid_categories = {'Query', 'Claim', 'Monthly Follow-up', 'Monthly Follow up', 'Urgent', 'Unsure'}
    if existing_classification and str(existing_classification).strip() in valid_categories:
        return str(existing_classification).strip()

    ct_lower = (call_type or '').lower()
    if 'claim' in ct_lower or 'termination' in ct_lower or 'ad-hoc' in ct_lower or 'ad hoc' in ct_lower:
        return 'Claim'
    if 'urgent' in ct_lower or 'complaint' in ct_lower or 'overdue' in ct_lower:
        return 'Urgent'
    if 'follow up' in ct_lower or 'follow-up' in ct_lower or 'monthly' in ct_lower:
        return 'Monthly Follow-up'
    return 'Query'


def _extract_mip_from_task_id(task_email_id, delegate_map):
    """Traces a task_email_id back to (mip_number, id_number) via prefix parsing or PssubfDelegate."""
    if not task_email_id:
        return '', ''

    tid = str(task_email_id).strip()

    # 1. Direct lookup in PssubfDelegate map (covers Outlook Graph email IDs)
    if tid in delegate_map:
        return delegate_map[tid]

    # 2. Extract MIP from prefixed keys: PROFILE_57218096, NOTE_57218096, DIRECT_57218096_12, CLAIM_57218096
    prefix_match = re.match(r'^(?:PROFILE_MOD_|PROFILE_|NOTE_|DIRECT_|CLAIM_)(\d+)', tid)
    if prefix_match:
        return prefix_match.group(1), ''

    return '', ''


@login_required
def pssubf_log_view(request):
    # Check if an edit_id was passed via GET parameters (from the beneficiary profile page)
    edit_id = request.GET.get('edit_id')
    edit_log = None
    if edit_id:
        try:
            edit_log = SystemLog.objects.get(id=edit_id)
        except SystemLog.DoesNotExist:
            pass

    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        if action_type == 'mark_complete':
            messages.success(request, "Task marked as complete.")
            return redirect('pssubf_log_page')

        log_id = request.POST.get('log_id')
        mip_number = request.POST.get('mip_number')
        call_direction = request.POST.get('call_direction')
        call_method = request.POST.get('call_method')
        call_type = request.POST.get('call_type')
        category = request.POST.get('category')
        content = request.POST.get('note_content')

        title = call_type if call_type else "General Note"
        status = "In Progress"

        if content:
            if log_id:
                try:
                    log_entry = SystemLog.objects.get(id=log_id)
                    log_entry.mip_number = mip_number
                    log_entry.log_title = title
                    log_entry.call_direction = call_direction
                    log_entry.call_method = call_method
                    log_entry.call_type = call_type
                    log_entry.category = category
                    log_entry.status = status
                    log_entry.note_content = content
                    log_entry.save()
                    messages.success(request, "Log entry updated successfully.")
                except SystemLog.DoesNotExist:
                    messages.error(request, "Error: The log entry could not be found.")
            else:
                SystemLog.objects.create(
                    mip_number=mip_number,
                    log_title=title,
                    call_direction=call_direction,
                    call_method=call_method,
                    call_type=call_type,
                    category=category,
                    status=status,
                    note_content=content,
                    created_by=request.user.username
                )
                messages.success(request, "New internal note saved successfully.")

            return redirect('pssubf_log_page')
        else:
            messages.error(request, "Note Content is required.")

    # --- 1. PARSE DATE RANGE FILTERS ---
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    action = request.GET.get('action')

    start_dt = None
    end_dt = None

    if date_from:
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
            try:
                parsed_from = datetime.strptime(date_from.strip(), fmt)
                naive_start = datetime.combine(parsed_from.date(), time.min)
                start_dt = timezone.make_aware(naive_start) if getattr(settings, 'USE_TZ', False) else naive_start
                break
            except ValueError:
                continue

    if date_to:
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
            try:
                parsed_to = datetime.strptime(date_to.strip(), fmt)
                naive_end = datetime.combine(parsed_to.date(), time.max)
                end_dt = timezone.make_aware(naive_end) if getattr(settings, 'USE_TZ', False) else naive_end
                break
            except ValueError:
                continue

    # --- 2. FETCH FROM SystemLog, PssubfNote, AND PssubfAction ---
    sys_qs = SystemLog.objects.all()
    notes_qs = PssubfNote.objects.filter(note_text__contains='[').filter(note_text__contains='|')
    actions_qs = PssubfAction.objects.filter(note_content__contains='[').filter(note_content__contains='|')

    if start_dt:
        sys_qs = sys_qs.filter(created_at__gte=start_dt)
        notes_qs = notes_qs.filter(created_at__gte=start_dt)
        actions_qs = actions_qs.filter(action_timestamp__gte=start_dt)

    if end_dt:
        sys_qs = sys_qs.filter(created_at__lte=end_dt)
        notes_qs = notes_qs.filter(created_at__lte=end_dt)
        actions_qs = actions_qs.filter(action_timestamp__lte=end_dt)

    sys_logs = list(sys_qs.order_by('-created_at'))
    note_rows = list(notes_qs.order_by('-created_at'))
    action_rows = list(actions_qs.order_by('-action_timestamp'))

    # Bulk lookup PssubfDelegate to resolve MIP & ID numbers for email-linked notes/actions
    email_ids_to_resolve = set()
    for n in note_rows:
        if n.task_email_id and not str(n.task_email_id).startswith(('PROFILE_', 'NOTE_', 'DIRECT_', 'CLAIM_')):
            email_ids_to_resolve.add(n.task_email_id)
    for a in action_rows:
        if a.task_email_id and not str(a.task_email_id).startswith(('PROFILE_', 'NOTE_', 'DIRECT_', 'CLAIM_')):
            email_ids_to_resolve.add(a.task_email_id)

    delegate_map = {}
    if email_ids_to_resolve:
        for d in PssubfDelegate.objects.filter(email_id__in=email_ids_to_resolve).only('email_id', 'member_group_code', 'id_number'):
            delegate_map[d.email_id] = (
                str(d.member_group_code or '').strip(),
                str(d.id_number or '').strip(),
            )

    # --- 3. MERGE, PARSE & DEDUPLICATE ---
    unified_logs = []
    seen_keys = set()

    def _dedup_key(mip, agent, direction, method, ctype, dt):
        ts_minute = dt.strftime('%Y-%m-%d %H:%M') if dt else ''
        return (
            str(mip or '').strip().lower(),
            str(agent or '').strip().lower(),
            str(direction or '').strip().lower(),
            str(method or '').strip().lower(),
            str(ctype or '').strip().lower(),
            ts_minute,
        )

    # A) Primary SystemLog records (always editable)
    for log in sys_logs:
        key = _dedup_key(log.mip_number, log.created_by, log.call_direction, log.call_method, log.call_type, log.created_at)
        seen_keys.add(key)
        unified_logs.append({
            'id': log.id,
            'is_editable': True,
            'source': 'SystemLog',
            'mip_number': log.mip_number or '',
            'id_number': getattr(log, 'id_number', '') or '',
            'call_direction': log.call_direction or '',
            'call_method': log.call_method or '',
            'call_type': log.call_type or '',
            'category': log.category or 'Query',
            'created_by': log.created_by or '',
            'note_content': log.note_content or '',
            'created_at': log.created_at,
        })

    # B) Matching PssubfNote records ([Direction | Method | Call Type] Content)
    for note in note_rows:
        match = BRACKETED_LOG_PATTERN.match(note.note_text or '')
        if not match:
            continue

        direction, method, call_type, clean_content = [g.strip() for g in match.groups()]
        mip_num, id_num = _extract_mip_from_task_id(note.task_email_id, delegate_map)
        key = _dedup_key(mip_num, note.agent_name, direction, method, call_type, note.created_at)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        unified_logs.append({
            'id': '',
            'is_editable': False,
            'source': 'PssubfNote',
            'mip_number': mip_num,
            'id_number': id_num,
            'call_direction': direction,
            'call_method': method,
            'call_type': call_type,
            'category': _infer_log_category(call_type, note.classification_at_time),
            'created_by': note.agent_name or '',
            'note_content': clean_content,
            'created_at': note.created_at,
        })

    # C) Matching PssubfAction records ([Direction | Method | Call Type] Content)
    for act in action_rows:
        match = BRACKETED_LOG_PATTERN.match(act.note_content or '')
        if not match:
            continue

        direction, method, call_type, clean_content = [g.strip() for g in match.groups()]
        mip_num, id_num = _extract_mip_from_task_id(act.task_email_id, delegate_map)
        key = _dedup_key(mip_num, act.action_user, direction, method, call_type, act.action_timestamp)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        unified_logs.append({
            'id': '',
            'is_editable': False,
            'source': 'PssubfAction',
            'mip_number': mip_num,
            'id_number': id_num,
            'call_direction': direction,
            'call_method': method,
            'call_type': call_type,
            'category': _infer_log_category(call_type),
            'created_by': act.action_user or '',
            'note_content': clean_content,
            'created_at': act.action_timestamp,
        })

    # Sort combined timeline newest first
    fallback_dt = timezone.now().replace(year=1900) if getattr(settings, 'USE_TZ', False) else datetime(1900, 1, 1)
    unified_logs.sort(key=lambda x: x['created_at'] if x['created_at'] else fallback_dt, reverse=True)

    # --- 4. EXCEL EXPORT (Matching PSSUBF Call Logs.xlsx with Beneficiary LEFT JOIN) ---
    if action == 'export':
        from openpyxl.styles import Font, Alignment

        lookup_keys = set()
        for log in unified_logs:
            if log['mip_number']:
                lookup_keys.add(str(log['mip_number']).strip())
            if log['id_number']:
                lookup_keys.add(str(log['id_number']).strip())

        beneficiaries_by_mip = {}
        beneficiaries_by_id = {}
        if lookup_keys:
            matched_beneficiaries = PssubfBeneficiary.objects.filter(
                Q(membership_number__in=lookup_keys) | Q(id_number__in=lookup_keys)
            ).only('membership_number', 'id_number', 'first_name', 'last_name')

            for b in matched_beneficiaries:
                if b.membership_number:
                    beneficiaries_by_mip[str(b.membership_number).strip()] = b
                if b.id_number:
                    beneficiaries_by_id[str(b.id_number).strip()] = b

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Call_Logs_{timezone.now().strftime('%Y-%m-%d %H_%M_%S')}"[:31]

        headers = [
            'A - Beneficiary Name Surname',
            'B - ID/Passport',
            'C - Created On',
            'D - Call Direction',
            'E - Call Method',
            'F - Call Type',
            'G - Created By',
            'H - MIP Number',
        ]
        ws.append(headers)

        header_font = Font(name='Aptos Narrow', size=11, bold=True, color='000000')
        for cell in ws[1]:
            cell.font = header_font
            cell.alignment = Alignment(horizontal='left', vertical='center')

        for log in unified_logs:
            raw_mip = str(log['mip_number']).strip()
            raw_id = str(log['id_number']).strip()

            b = (
                beneficiaries_by_mip.get(raw_mip)
                or beneficiaries_by_id.get(raw_mip)
                or beneficiaries_by_id.get(raw_id)
            )

            beneficiary_name = f"{b.first_name or ''} {b.last_name or ''}".strip() if b else ''
            id_passport = (b.id_number if b and b.id_number else raw_id) or ''
            mip_out = (b.membership_number if b and b.membership_number else raw_mip) or ''

            created_on = None
            if log['created_at']:
                dt_local = timezone.localtime(log['created_at']) if timezone.is_aware(log['created_at']) else log['created_at']
                created_on = dt_local.replace(tzinfo=None)

            ws.append([
                beneficiary_name,              # A - Beneficiary Name Surname
                str(id_passport),              # B - ID/Passport
                created_on,                    # C - Created On
                log['call_direction'],         # D - Call Direction
                log['call_method'],            # E - Call Method
                log['call_type'],              # F - Call Type
                log['created_by'],             # G - Created By
                mip_out,                       # H - MIP Number
            ])

            r_idx = ws.max_row
            ws.cell(r_idx, 2).number_format = '@'
            if created_on:
                ws.cell(r_idx, 3).number_format = 'yyyy-mm-dd hh:mm:ss'

        for col in ws.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col:
                if cell.value is not None:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 14), 45)

        if date_from and date_to:
            filename = f"PSSUBF Call Logs {date_from} to {date_to}.xlsx"
        else:
            filename = f"PSSUBF Call Logs {date.today().strftime('%d.%m.%Y')}.xlsx"

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response

    # --- 5. PAGINATION (36 records per page) ---
    paginator = Paginator(unified_logs, 36)
    page_number = request.GET.get('page')
    recent_logs = paginator.get_page(page_number)

    return render(request, 'pssubf/Log.html', {
        'recent_logs': recent_logs,
        'edit_log': edit_log,
        'date_from': date_from or '',
        'date_to': date_to or ''
    })


@login_required
def outlook_dashboard_view(request):
    # Any user logged into an account can open this dashboard cleanly.

    target_email = request.GET.get('email', settings.OUTLOOK_EMAIL_ADDRESS)
    search_query = request.GET.get('q', '').strip().lower()
    sort_order = request.GET.get('sort', 'newest')
    
    # 1. Fetch live data from Graph API
    inbox_data = OutlookGraphService.fetch_inbox_messages(target_email, top_count=50) 
    
    if 'error' in inbox_data:
        return render(request, 'pssubf/inbox_list.html', {'error': inbox_data['error']})

    all_emails = inbox_data.get('value', [])
    email_ids = [e['id'] for e in all_emails]

    # 2. Bulk fetch existing records to reduce DB hits
    local_inbox_map = PssubfInbox.objects.filter(email_id__in=email_ids).in_bulk(field_name='email_id')
    delegated_map = PssubfDelegate.objects.filter(email_id__in=email_ids).in_bulk(field_name='email_id')

    filtered_emails = []
    
    # Get the currently logged-in user's username
    current_username = request.user.username

    for email in all_emails:
        e_id = email['id']
        
        # --- SECURITY & RECYCLE BIN FILTERING START ---
        if e_id in delegated_map:
            delegation_record = delegated_map[e_id]
            
            # Immediately skip if marked as Recycled or permanently deleted
            if delegation_record.status in ['Recycled', 'PERM_DEL']:
                continue
            
            # 1. Skip if already processed (anything not 'Assigned' is considered archived/done)
            if delegation_record.status != 'Assigned':
                continue
                
            # 2. HIDE OTHER AGENTS' TASKS
            # If the task has an assigned agent, and it is NOT the person currently logged in, skip it.
            # (Superusers/Admins bypass this and see everything)
            if delegation_record.assigned_agent and delegation_record.assigned_agent != current_username:
                if not request.user.is_superuser:
                    continue
        else:
            # Check if it was marked PERM_DEL in Inbox previously
            inbox_check = local_inbox_map.get(e_id)
            if inbox_check and inbox_check.status == 'PERM_DEL':
                continue
        # --- SECURITY FILTERING END ---

        # Sync PssubfInbox (The Archive) - Safe get_or_create prevents duplicate key errors
        if e_id not in local_inbox_map:
            received_date = email.get('receivedDateTime')
            safe_subject = email.get('subject') or '(No Subject)'
            
            local_record, created = PssubfInbox.objects.get_or_create(
                email_id=e_id,
                defaults={
                    'subject': safe_subject,
                    'sender': email.get('from', {}).get('emailAddress', {}).get('address', '').lower(),
                    'received_timestamp': date_parser.isoparse(received_date) if received_date else timezone.now(),
                    'snippet': email.get('bodyPreview', '') or '',
                    'status': 'Pending'
                }
            )
        else:
            local_record = local_inbox_map[e_id]

        # Sync PssubfDelegate (The Active Task List) - Safe get_or_create prevents duplicate key errors
        if e_id not in delegated_map:
            delegation, created = PssubfDelegate.objects.get_or_create(
                email_id=e_id,
                defaults={
                    'status': 'Assigned',
                    'subject': local_record.subject or '(No Subject)',
                    'sender': local_record.sender,
                }
            )
        else:
            delegation = delegated_map[e_id]
            if delegation.status in ['Recycled', 'PERM_DEL']:
                continue

        # Prepare for Template
        email_display = {
            'id': e_id,
            'subject': local_record.subject or '(No Subject)',
            'sender': local_record.sender,
            'received_at': local_record.received_timestamp,
            'snippet': local_record.snippet,
            'status': delegation.status,
            'assigned_agent': delegation.assigned_agent,
        }

        # Search Filter
        if search_query:
            subj_lower = (email_display['subject'] or '').lower()
            sender_lower = (email_display['sender'] or '').lower()
            content = f"{subj_lower} {sender_lower}"
            if search_query not in content:
                continue

        filtered_emails.append(email_display)

    # 3. Sort
    reverse_sort = (sort_order == 'newest')
    filtered_emails.sort(key=lambda x: x['received_at'] if x['received_at'] else timezone.now(), reverse=reverse_sort)

    return render(request, 'pssubf/inbox_list.html', {
        'messages': filtered_emails,
        'search_query': search_query,
        'sort_order': sort_order,
        'target_email': target_email
    })

def pssubf_delegate_view(request, email_id):
    """View to fetch live email details and delegate tasks or log internal notes."""
    
    # Decode the URL-encoded email ID to prevent lookup mismatches
    email_id = unquote(email_id)

    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    available_users = User.objects.filter(is_active=True)

    # Fetch reference to local inbox and delegate task data
    inbox_item = PssubfInbox.objects.filter(email_id=email_id).first()
    task = PssubfDelegate.objects.filter(email_id=email_id).first()
    
    # Check if the user is Vanessa (Manager override check)
    is_vanessa = request.user.username.lower() in ['vanessa', 'admin', 'luanovaneck']

    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        # --- 1. HANDLE INTERNAL NOTE / QUICK LOG SUBMISSION ---
        if action_type == 'add_note':
            call_direction = request.POST.get('call_direction', 'Inbound').strip()
            call_method = request.POST.get('call_method', 'Phone')
            call_type = request.POST.get('call_type', 'General Query')
            note_content = request.POST.get('note_content', '')
            email_category = request.POST.get('email_category', task.email_category if task else 'Query')
            status = request.POST.get('status', task.status if task else 'In Progress')

            action_type_label = 'Outbound Note' if call_direction == 'Outbound' else 'Inbound Note'

            mip_code = task.member_group_code if task else None
            id_num = task.id_number if task else None

            SystemLog.objects.create(
                mip_number=mip_code,
                id_number=id_num,
                log_title=f"{call_direction} - {call_method}: {call_type[:40]}",
                call_direction=call_direction, 
                call_method=call_method,
                call_type=call_type,
                category=email_category if email_category in dict(SystemLog.CATEGORY_CHOICES) else 'Query',
                status=status,
                note_content=note_content,
                created_by=request.user.username
            )

            PssubfAction.objects.create(
                task_email_id=email_id,
                action_type=action_type_label,
                action_user=request.user.username,
                note_content=f"[{call_direction} | {call_method}] {note_content}",
                action_timestamp=timezone.now()
            )

            if task:
                task.email_category = email_category
                task.status = status
                task.save()

            messages.success(request, f"[{call_direction}] Internal note and Quick Log saved successfully.")
            return redirect('pssubf_action', email_id=email_id)

        # --- 2. HANDLE TASK METADATA UPDATE ---
        elif action_type == 'update_metadata':
            if task:
                task.member_group_code = request.POST.get('member_group_code', task.member_group_code)
                task.email_category = request.POST.get('email_category', task.email_category)
                task.status = request.POST.get('status', task.status)
                task.save()
                messages.success(request, "Task metadata updated successfully.")
            return redirect('pssubf_action', email_id=email_id)

        # --- 3. HANDLE MARK COMPLETE ---
        elif action_type == 'mark_complete':
            if task:
                task.status = 'Completed'
                task.save()
            if inbox_item:
                inbox_item.status = 'Completed'
                inbox_item.save()
            messages.success(request, "Task marked as complete.")
            return redirect('pssubf_dashboard')

        # --- 4. DEFAULT DELEGATION SUBMISSION ---
        else:
            agent_name = request.POST.get('assigned_agent')
            is_recycle = 'recycle' in request.POST
            
            form_data = request.POST.copy()
            
            # 🟢 Fallback handling for fields hidden/commented out in the template
            if not form_data.get('member_group_code') and task:
                form_data['member_group_code'] = task.member_group_code or ''
            if not form_data.get('email_category') and task:
                form_data['email_category'] = task.email_category or 'Query'
            elif not form_data.get('email_category'):
                form_data['email_category'] = 'Query'

            provided_mip = form_data.get('member_group_code', '').strip()
            provided_id = form_data.get('id_number', '').strip()
            
            if provided_id and not provided_mip:
                beneficiary = PssubfBeneficiary.objects.filter(id_number=provided_id).first()
                if beneficiary and beneficiary.membership_number:
                    form_data['member_group_code'] = beneficiary.membership_number
                    
            elif provided_mip and not provided_id:
                beneficiary = PssubfBeneficiary.objects.filter(membership_number=provided_mip).first()
                if beneficiary and beneficiary.id_number:
                    form_data['id_number'] = beneficiary.id_number

            success, message = delegate_pssubf_task(
                email_id=email_id,
                agent_name=agent_name,
                delegator_user=request.user,
                form_data=form_data, 
                is_recycle=is_recycle
            )
            
            if success:
                if inbox_item:
                    inbox_item.status = 'Recycled' if is_recycle else 'Delegated'
                    inbox_item.save()

                messages.success(request, message)
                return redirect('pssubf_dashboard')
            else:
                messages.error(request, f"Error: {message}")

    # Fetch live content for the detail view
    email_data = OutlookGraphService._make_graph_request(f"messages/{email_id}", method='GET')
    
    if isinstance(email_data, dict) and 'error' in email_data:
        email_subject = inbox_item.subject if inbox_item else "Error"
        email_content = inbox_item.snippet if inbox_item else "Content Unavailable"
        attachments = []
    else:
        email_subject = email_data.get('subject', '(No Subject)')
        email_content = email_data.get('body', {}).get('content', '')
        attachments = OutlookGraphService.fetch_attachments(target_email, email_id)
        
        for att in attachments:
            if att.get('isInline') and att.get('contentId'):
                cid = att.get('contentId')
                raw = OutlookGraphService.get_attachment_raw(target_email, email_id, att['id'])
                if raw and isinstance(raw, dict) and 'contentBytes' in raw:
                    data_url = f"data:{att.get('contentType', 'image/png')};base64,{raw['contentBytes']}"
                    email_content = email_content.replace(f"cid:{cid}", data_url)
                    att['contentBytes'] = raw['contentBytes']

    return render(request, 'pssubf/delegate.html', {
        'email_id': email_id,
        'email_subject': email_subject,
        'email_content': email_content,
        'attachments': attachments,
        'available_users': available_users,
        'inbox_item': inbox_item,
        'task': task,
        'is_vanessa': is_vanessa,
        # 🟢 Pass received date and sender from inbox item
        'received_timestamp': inbox_item.received_timestamp if inbox_item else None,
        'sender': inbox_item.sender if inbox_item else ''
    })

logger = logging.getLogger(__name__)

from .models import SystemLog, PssubfNote, PssubfAction, PssubfDirectEmail, PssubfDelegate, PssubfInbox

logger = logging.getLogger(__name__)

@login_required
def pssubf_action_view(request, email_id):
    """
    Agent Action View: Handles Notes, Metadata Updates, Completion, 
    and Email Replies while resolving broken inline images.
     
    Dynamically routes system-generated tracking logs (PROFILE_MOD_, NOTE_, etc.)
    by bypassing Graph API calls while rendering authentic database action responses,
    history chains, and historical audit content.
    """
    # 🟢 Decode the URL-encoded email ID to prevent lookup mismatches and 404 errors
    email_id = unquote(email_id)

    is_direct_entry = False
    is_system_log = False
    attachments = []
    email_content = ""
    email_subject = "(No Subject)"
     
    # 🟢 BULLETPROOF CHECK: Strip invisible spaces and force lowercase
    current_user_clean = request.user.username.strip().lower()
    is_vanessa = (current_user_clean == 'vanessa') or request.user.is_superuser
     
    available_users = User.objects.filter(is_active=True) if is_vanessa else []
     
    # --- 1. DETECT AND INTERCEPT ADMINISTRATIVE SYSTEM LOG STRINGS ---
    if any(str(email_id).startswith(prefix) for prefix in ["PROFILE_MOD_", "PROFILE_"]):
        is_system_log = True
        clean_numeric_id = str(email_id).replace("PROFILE_MOD_", "").replace("PROFILE_", "").replace("NOTE_", "")
         
        # Look into the action history ledger table to pull the earliest logged item for this ID
        first_action_occurrence = PssubfAction.objects.filter(task_email_id=email_id).order_by('action_timestamp').first()
         
        # Build synthetic mock task wrapper context object to satisfy template layout elements safely
        class VirtualSystemTask:
            def __init__(self):
                self.email_id = email_id
                self.status = "System Log Reference"
                self.email_category = "System Audit"
                self.member_group_code = "N/A"
                # Inherit subject line context from matching record if it exists
                self.subject = f"System Log Activity Stream [Ref: #{clean_numeric_id}]"
                self.snippet = first_action_occurrence.note_content if first_action_occurrence else f"Automated audit entry registered under Reference Key: {clean_numeric_id}."
         
        task = VirtualSystemTask()
        email_subject = task.subject
         
        # Render the logged note/reply action content right into the primary detail content container block
        if first_action_occurrence:
            # Re-format carriage breaks nicely into readable paragraphs for html
            formatted_snippet = first_action_occurrence.note_content.replace('\n', '<br>')
            email_content = f"<div class='p-2' style='font-family: monospace; white-space: pre-wrap;'>{formatted_snippet}</div>"
        else:
            email_content = f"<p><strong>Internal Verification Ledger Panel</strong></p><p>{task.snippet}</p>"

    else:
        # --- 2. STANDARD RUNTIME WORKFLOW: RESOLVE PHYSICAL DATA TASK SOURCE ---
        task = PssubfDelegate.objects.filter(email_id=email_id).first()

        if not task:
            task = PssubfInbox.objects.filter(email_id=email_id).first()
            is_direct_entry = True

        if not task:
            # Fallback check: If history logs exist for this un-prefixed record, build a fallback structure
            if PssubfAction.objects.filter(task_email_id=email_id).exists():
                class GenericTaskFallback:
                    def __init__(self):
                        self.email_id = email_id
                        self.status = "Audit Line Only"
                        self.email_category = "General Activity"
                        self.member_group_code = "N/A"
                        self.subject = f"Activity Tracking Log [ID: {email_id}]"
                task = GenericTaskFallback()
                email_subject = task.subject
                email_content = "<p><strong>System Action Tracker</strong></p><p>Review full operations history data via the visual action ledger tracking pane layout below.</p>"
                is_system_log = True
            else:
                raise Http404("No record found for this ID in Delegations, Inbox, or System History tables.")

        target_email = settings.OUTLOOK_EMAIL_ADDRESS 

    # 🟢 TERMINAL DEBUGGER: View this in your VS Code terminal when reloading the page
    #print(f"--- DEBUG VANESSA ACCESS ---")
    #print(f"Cleaned Username: '{current_user_clean}'")
    #print(f"is_vanessa Evaluated To: {is_vanessa}")
    #print(f"is_system_log Evaluated To: {is_system_log}")
    #print(f"Task ID Clicked: {email_id}")
    #print(f"-----------------------------")

    # --- POST Logic ---
    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        # 🟢 RE-DELEGATE OVERRIDE FOR VANESSA (Redirects to audit logs upon success)
        if action_type == 'redelegate' and is_vanessa:
            new_agent = request.POST.get('assigned_agent')
            if new_agent:
                success, message = delegate_pssubf_task(
                    email_id=email_id,
                    agent_name=new_agent,
                    delegator_user=request.user,
                    form_data=request.POST,
                    is_recycle=False
                )
                if success:
                    # Keep local inbox updated if it exists
                    inbox_item = PssubfInbox.objects.filter(email_id=email_id).first()
                    if inbox_item:
                        inbox_item.status = 'Delegated'
                        inbox_item.save()
                    messages.success(request, f"Manager Override: Task re-delegated to {new_agent}.")
                    return redirect('pssubf_audit_logs')
                else:
                    messages.error(request, f"Error re-delegating: {message}")
            return redirect('pssubf_action', email_id=email_id)

        if is_system_log:
            messages.error(request, "Modifying system baseline log entries directly is prohibited.")
            return redirect('pssubf_action', email_id=email_id)

        # 1. Update Metadata
        elif action_type == 'update_metadata':
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
            new_category = request.POST.get('email_category')
            new_status = request.POST.get('status')
             
            # FORCE direction to Inbound for internal task notes
            call_direction = "Inbound"
            call_method = request.POST.get('call_method', 'Note')
            call_type = request.POST.get('call_type', 'General Note')
             
            if new_category:
                task.email_category = new_category
            if new_status:
                task.status = new_status
            task.save()

            mip_number = getattr(task, 'member_group_code', None) or ''
             
            # --- PUSH TO SYSTEM LOG (Beneficiary Page) ---
            SystemLog.objects.create(
                mip_number=mip_number,
                log_title="Task Action Note",
                call_direction=call_direction,
                call_method=call_method,
                call_type=call_type,
                category=new_category or getattr(task, 'email_category', 'Query'),
                status=new_status or getattr(task, 'status', 'In Progress'),
                note_content=note_text,
                created_by=request.user.username
            )
             
            audit_string = f"[{call_direction} | {call_method} | {call_type}]"
             
            # --- PUSH TO PSSUBF NOTE (Thread History) ---
            PssubfNote.objects.create(
                task_email_id=email_id,
                agent_name=request.user.username,
                note_text=f"{audit_string} {note_text}",
                classification_at_time=getattr(task, 'email_category', 'N/A'),
                status_at_time=task.status
            )

            PssubfAction.objects.create(
                task_email_id=email_id,
                action_user=request.user.username,
                action_type="NOTE",
                note_content=f"{audit_string} {note_text}"
            )
            messages.success(request, "Internal note saved.")

        # 3. Handle External Email Reply (Updated with Popup Modal Options)
        elif action_type == 'send_reply':
            recipient = request.POST.get('reply_recipient')
            cc_recipient = request.POST.get('reply_cc', '').strip()
            bcc_recipient = request.POST.get('reply_bcc', '').strip()
            subject = request.POST.get('reply_subject')
            raw_body_content = request.POST.get('reply_body')
             
            # Extract outbound metadata coming from popup modal
            call_direction = "Outbound"
            call_method = request.POST.get('call_method', 'Emails')
            call_type = request.POST.get('call_type', 'Feedback to Beneficiary')
            new_category = request.POST.get('email_category')
            new_status = request.POST.get('status')

            # Update task metadata if changed
            if task:
                if new_category:
                    task.email_category = new_category
                if new_status:
                    task.status = new_status
                task.save()

            # Format the email body to preserve paragraphs
            body_content = format_email_body(raw_body_content)

            uploaded_files = request.FILES.getlist('reply_attachments')
            attachments_payload = []
            file_saved_path = None
             
            for idx, f in enumerate(uploaded_files):
                content_bytes = f.read()
                f.seek(0) # Reset file pointer for local saving
                 
                # Save the first attachment locally for database thread reference
                if idx == 0:
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                    file_saved_path = fs.save(f.name, f)
                 
                try:
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
                cc=cc_recipient,
                bcc=bcc_recipient,
                subject=subject,
                body=body_content,
                attachments=attachments_payload,
                user=request.user
            )

            if isinstance(response, dict) and 'error' in response:
                messages.error(request, f"Email failed: {response.get('error')}")
            else:
                audit_string = f"[{call_direction} | {call_method} | {call_type}]"
                 
                # Build dynamic log string for CC/BCC to keep audit trails clean if empty
                cc_log = f"\nCC: {cc_recipient}" if cc_recipient else ""
                bcc_log = f"\nBCC: {bcc_recipient}" if bcc_recipient else ""

                mip_number = getattr(task, 'member_group_code', None) or ''
                 
                # --- PUSH TO SYSTEM LOG (Beneficiary Page) AS OUTBOUND ---
                SystemLog.objects.create(
                    mip_number=mip_number,
                    log_title="External Email Reply (Outbound)",
                    call_direction=call_direction,
                    call_method=call_method,
                    call_type=call_type,
                    category=new_category or getattr(task, 'email_category', 'Query'),
                    status=new_status or getattr(task, 'status', 'In Progress'),
                    note_content=f"REPLY SENT TO {recipient}{cc_log}{bcc_log}:\n{raw_body_content}",
                    created_by=request.user.username
                )

                # Log the outgoing reply into the direct email table
                PssubfDirectEmail.objects.create(
                    agent_name=request.user.username,
                    recipient=recipient,
                    subject=subject,
                    body_html=body_content,
                    sent_at=timezone.now(),
                    membership_number=mip_number,
                    attachment_path=file_saved_path
                )
                 
                PssubfAction.objects.create(
                    task_email_id=email_id,
                    action_user=request.user.username,
                    action_type="EMAIL_REPLY",
                    note_content=f"{audit_string}\nTo: {recipient}{cc_log}{bcc_log}\nSubject: {subject}\n\n{raw_body_content}"
                )

                # --- PUSH TO PSSUBF NOTE (Thread History) ---
                PssubfNote.objects.create(
                    task_email_id=email_id,
                    agent_name=request.user.username,
                    note_text=f"{audit_string} REPLY SENT TO {recipient}{cc_log}{bcc_log}: {raw_body_content}",
                    classification_at_time=new_category or getattr(task, 'email_category', 'N/A'),
                    status_at_time=new_status or getattr(task, 'status', 'In Progress')
                )
                messages.success(request, "Reply sent, logged as an Outbound note, and recorded successfully.")

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

    # --- 3. GET Logic: Only query Microsoft Graph API for non-system workflow IDs ---
    if not is_system_log:
        email_subject = getattr(task, 'subject', '(No Subject)')
        if not str(email_id).startswith("DIRECT_"):
            try:
                email_data = OutlookGraphService._make_graph_request(f"messages/{email_id}", method='GET')
                attachments = OutlookGraphService.fetch_attachments(target_email, email_id)
                email_content = email_data.get('body', {}).get('content', 'Content unavailable.')
                email_subject = email_data.get('subject', email_subject)

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
            except Exception as e:
                logger.error(f"Graph API Error: {e}")
                email_content = "Could not retrieve email body from Outlook. This may be a local-only record."
        else:
            email_content = f"<p><strong>Internal Communication Record</strong></p><p>{getattr(task, 'snippet', 'No content available.')}</p>"

    # Fetch complete historical ledger timeline (applies uniformly for tracking historical logs)
    history = PssubfAction.objects.filter(task_email_id=email_id).order_by('-action_timestamp')

    return render(request, 'pssubf/action_detail.html', {
        'task': task,
        'email_subject': email_subject,
        'email_content': email_content,
        'attachments': attachments,
        'history': history,
        'email_id': email_id,
        'is_direct': is_direct_entry,
        'is_system_log': is_system_log,
        'is_vanessa': is_vanessa,
        'available_users': available_users
    })


@login_required
def pssubf_view_thread(request, email_id):
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    email_data = {}
    attachments = []
    # 1. Determine if this is a local Direct Email or a Graph API email
    is_direct = str(email_id).startswith('DIRECT_')
    local_email = None
    email_body = "Could not retrieve content. (Email may have been moved or deleted)."
    if is_direct:
        # --- HANDLE LOCAL DIRECT EMAILS (As root) ---
        try:
            db_id = str(email_id).split('_')[-1]
            local_email = PssubfDirectEmail.objects.get(id=db_id)
            email_body = getattr(local_email, 'body_html', '')
            email_data = {
                'id': email_id,
                'subject': local_email.subject,
                'from': {
                    'emailAddress': {
                        'name': getattr(local_email, 'agent_name', request.user.username),
                        'address': target_email
                    }
                },
                'receivedDateTime': local_email.sent_at if hasattr(local_email, 'sent_at') else timezone.now().isoformat()
            }
            
            # Check for local attachment on the root direct email
            if hasattr(local_email, 'attachment_path') and local_email.attachment_path:
                filename = os.path.basename(str(local_email.attachment_path))
                attachments.append({
                    'id': 'local',
                    'name': filename,
                    'isInline': False,
                    'contentType': 'application/octet-stream',
                    'local_url': f"{settings.MEDIA_URL}{local_email.attachment_path}"
                })
        except Exception as e:
            email_data = {'subject': 'Error loading local email', 'id': email_id}
            email_body = str(e)
    else:
        # --- HANDLE STANDARD OUTLOOK EMAILS (As root) ---
        try:
            response = OutlookGraphService._make_graph_request(f"messages/{email_id}", method='GET')
            if response and 'error' not in response:
                email_data = response
                email_body = email_data.get('body', {}).get('content', '')    
                # Fetch attachments
                atts = OutlookGraphService.fetch_attachments(target_email, email_id)
                if atts:
                    for att in atts:
                        content_type = att.get('contentType', 'image/png').lower()
                        # Replace CID with Base64 for inline images
                        if att.get('isInline') and att.get('contentId'):
                            cid = att.get('contentId')
                            raw_data = OutlookGraphService.get_attachment_raw(target_email, email_id, att['id'])
                            if raw_data and 'contentBytes' in raw_data:
                                base64_data = raw_data['contentBytes']
                                email_body = email_body.replace(f"cid:{cid}", f"data:{content_type};base64,{base64_data}")
                        attachments.append(att)
            else:
                email_data = {'subject': 'Email Not Found in Outlook', 'id': email_id}
        except Exception as e:
            logger.error(f"Error in pssubf_view_thread fetching graph: {e}")
            email_data = {'subject': 'Error Loading Email', 'id': email_id}

    # 2. Build Unified Timeline (Audit Trail + Replies)
    actions = list(PssubfAction.objects.filter(task_email_id=email_id).order_by('-action_timestamp'))
    
    # Fetch related local outbound emails/replies sharing the same thread subject
    subject = email_data.get('subject', 'No Subject')
    clean_subject = subject.replace("RE: ", "").replace("Re: ", "").replace("FW: ", "").replace("Fw: ", "").strip()   
    outbound_replies = []
    if clean_subject and clean_subject != "No Subject":
        qs = PssubfDirectEmail.objects.filter(subject__icontains=clean_subject)
        # Exclude the root email if it is a local direct email to avoid duplicating it in the replies stream
        if is_direct and local_email:
            qs = qs.exclude(id=local_email.id)
        outbound_replies = list(qs)
    combined_timeline = []
    # Add Audit Actions to Timeline
    for act in actions:
        combined_timeline.append({
            'type': 'action',
            'date': act.action_timestamp,
            'obj': act
        })
        
    # Add Replies to Timeline
    for rep in outbound_replies:
        agent_username = getattr(rep, 'agent_name', 'Agent')
        name_mapping = {
            'LuanovanEck': 'Luano van Eck',
            'Testuser1': 'Test Agent',
            'omega': 'Omega System Assistant',
        }
        full_name = name_mapping.get(agent_username, agent_username.replace('_', ' ').title())

        # Fix formatting for simple textareas
        raw_body = getattr(rep, 'body_html', '').replace('\r\n', '<br>').replace('\n', '<br>')
        
        # Standardize Signature Mirror
        signature_html = f"""
        <br><br>
        <div style="font-family: Arial, sans-serif; font-size: 13px; color: #333; margin-top: 20px; border-top: 1px solid #ccc; padding-top: 10px;">
            <table cellpadding="0" cellspacing="0" border="0" style="width: 100%;">
                <tr>
                        <p style="margin: 0 0 4px 0; font-size: 14px;"><strong style="color: #1b5e20;">{full_name}</strong></p>
                        <p style="margin: 0 0 6px 0; font-size: 12px; color: #555;">PSSUBF Beneficiary Operations</p>
                    <td style="padding-right: 20px; vertical-align: top; width: 160px;">
                        <img src="https://futurasa.co.za/wp-content/uploads/2023/10/Futura-Logo.png" alt="Futura Logo" style="width: 150px; display: block;">
                    </td>
                    <td style="vertical-align: top;">
                        <p style="margin: 0 0 4px 0;"><strong>phone:</strong> 087 702 5950</p>
                        <p style="margin: 0 0 4px 0;"><strong>fax:</strong> 086 225 2554</p>
                        <p style="margin: 0 0 0 0;"><strong>Email:</strong> <a href="mailto:pssbf@futurasa.co.za" style="color: #2e7d32;">pssbf@futurasa.co.za</a></p>
                    </td>
                </tr>
            </table>
        </div>
        """
        rep_attachment_url = None
        if hasattr(rep, 'attachment_path') and rep.attachment_path:
            rep_attachment_url = f"{settings.MEDIA_URL}{rep.attachment_path}"
            
        combined_timeline.append({
            'type': 'reply',
            'date': rep.sent_at,
            'obj': rep,
            'full_name': full_name,
            'formatted_body': raw_body + signature_html,
            'attachment_url': rep_attachment_url
        })
    # Sort timeline chronologically (Newest items First)
    # Using a safe fallback date (year 1900) so records missing a timestamp don't crash the sorter
    # and safely drop to the very bottom of the timeline.
    fallback_date = timezone.now().replace(year=1900)
    combined_timeline.sort(key=lambda x: x['date'] if x['date'] else fallback_date, reverse=True)
    context = {
        'email': email_data,
        'email_body': email_body,
        'attachments': attachments,
        'combined_timeline': combined_timeline,
        'is_direct': is_direct
    }
    return render(request, 'pssubf/thread_history.html', context)

from .services.token_manager import get_current_access_token

@login_required
def download_pssubf_attachment(request, message_id, attachment_id):
    """
    Streams raw binary attachment content directly from Graph API to user browser.
    Peak memory utilization stays under 10 KB regardless of file size (e.g. 30 MB+).
    """
    access_token = get_current_access_token()
    if not access_token:
        messages.error(request, "Failed to authenticate with Microsoft Graph API.")
        return redirect(request.META.get('HTTP_REFERER', 'pssubf_dashboard'))

    headers = {'Authorization': f'Bearer {access_token}'}
    base_attachment_url = f"https://graph.microsoft.com/v1.0/users/{settings.OUTLOOK_EMAIL_ADDRESS}/messages/{message_id}/attachments/{attachment_id}"

    # 1. Retrieve filename and MIME type using lightweight metadata query
    meta_params = {'$select': 'name,contentType'}
    
    try:
        meta_res = requests.get(base_attachment_url, headers=headers, params=meta_params, timeout=30)
        if meta_res.status_code != 200:
            logger.error(f"Graph attachment metadata failed (HTTP {meta_res.status_code}): {meta_res.text}")
            raise Http404("Attachment metadata not found.")
            
        meta_data = meta_res.json()
        raw_name = meta_data.get('name', 'attachment.bin')
        content_type = meta_data.get('contentType', 'application/octet-stream')

        # 2. Open binary connection stream to Graph /$value endpoint
        value_url = f"{base_attachment_url}/$value"
        graph_stream = requests.get(value_url, headers=headers, stream=True, timeout=30)

        if graph_stream.status_code != 200:
            logger.error(f"Graph binary stream failed (HTTP {graph_stream.status_code}): {graph_stream.text}")
            raise Http404("Failed to retrieve attachment binary stream.")

        # 3. Stream binary response in 8192-byte chunks directly to browser
        response = StreamingHttpResponse(
            graph_stream.iter_content(chunk_size=8192),
            content_type=content_type
        )
        
        encoded_filename = quote(raw_name)
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
        return response

    except requests.exceptions.Timeout:
        logger.error(f"Timeout (30s) reached while downloading attachment {attachment_id}")
        messages.error(request, "The attachment download timed out. Microsoft Graph API did not respond in time.")
        return redirect(request.META.get('HTTP_REFERER', 'pssubf_dashboard'))
    except Exception as e:
        logger.error(f"Unhandled attachment stream error: {e}")
        raise Http404("Error downloading attachment.")

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
    Only user 'omega' sees all active tasks; all other agents only see their own.
    """
    current_username = request.user.username.strip().lower()
    
    if current_username == 'omega':
        # User 'omega' sees all active tasks across the system
        delegations = PssubfDelegate.objects.exclude(
            status__in=['Recycled', 'Completed', 'Complete']
        ).order_by('-created_at')
    else:
        # All other agents ONLY see tasks assigned to them
        delegations = PssubfDelegate.objects.filter(
            assigned_agent__iexact=request.user.username
        ).exclude(
            status__in=['Recycled', 'Completed', 'Complete']
        ).order_by('-created_at')
    
    # Enrich delegation objects using custom attributes to avoid property assignment errors
    for task in delegations:
        inbox_match = PssubfInbox.objects.filter(email_id=task.email_id).first()
        task.display_received_timestamp = inbox_match.received_timestamp if inbox_match and inbox_match.received_timestamp else getattr(task, 'created_at', timezone.now())
        task.display_sender = task.sender or (inbox_match.sender if inbox_match else 'Unknown Sender')
        task.has_replied = PssubfAction.objects.filter(task_email_id=task.email_id, action_type="EMAIL_REPLY").exists()

    return render(request, 'pssubf/delegations_list.html', {
        'delegations': delegations
    })

import openpyxl
from django.http import HttpResponse
from datetime import datetime, time
from django.utils.timezone import make_aware, localtime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import PssubfAction, PssubfDelegate

import openpyxl
from django.http import HttpResponse
from datetime import datetime, time
from django.utils.timezone import make_aware, localtime, is_aware
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import PssubfAction, PssubfDelegate

@login_required
def pssubf_audit_logs(request):
    """
    Master Audit Log: Shows delegation logs with email details.
    Includes an export-to-Excel (XLSX) function that respects applied filters.
    Excludes Recycled records. Filters by email received date.
    """
    query = request.GET.get('q', '').strip()
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    is_export = request.GET.get('export') == 'excel'

    # 🟢 1. Annotate or fetch related PssubfInbox items to filter by received_timestamp
    inbox_qs = PssubfInbox.objects.all()

    if start_date_str:
        try:
            start_d = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            start_dt = make_aware(datetime.combine(start_d, time.min))
            inbox_qs = inbox_qs.filter(received_timestamp__gte=start_dt)
        except ValueError:
            pass

    if end_date_str:
        try:
            end_d = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            end_dt = make_aware(datetime.combine(end_d, time.max))
            inbox_qs = inbox_qs.filter(received_timestamp__lte=end_dt)
        except ValueError:
            pass

    # Get the list of email_ids that fall within the received date range
    filtered_email_ids = inbox_qs.values_list('email_id', flat=True)

    # Query delegations and exclude Recycled items
    logs = PssubfDelegate.objects.exclude(status='Recycled').order_by('-created_at')

    # 🟢 2. Apply the received date filter to the logs queryset
    if start_date_str or end_date_str:
        logs = logs.filter(email_id__in=filtered_email_ids)

    # Apply Search Filter
    if query:
        logs = logs.filter(
            Q(assigned_agent__icontains=query) |
            Q(subject__icontains=query) |
            Q(status__icontains=query) |
            Q(sender__icontains=query)
        )

    # Enrich delegation objects with inbox fallback details and sender info
    for log in logs:
        # Match with Inbox to get Received Date and Sender details if missing on delegation row
        inbox_match = PssubfInbox.objects.filter(email_id=log.email_id).first()
        received_ts = inbox_match.received_timestamp if inbox_match and inbox_match.received_timestamp else None
        
        # Capture From Email Address (Fallback to Inbox sender if delegation model doesn't store it)
        log.from_email = getattr(log, 'sender', None) or (inbox_match.sender if inbox_match else "Unknown")
        
        # Format Received Date
        if received_ts:
            dt_received = localtime(received_ts) if is_aware(received_ts) else received_ts
            log.display_received_date = dt_received.strftime("%d %b %Y %H:%M:%S")
            log.excel_received_date = dt_received.strftime("%Y-%m-%d %H:%M:%S")
        else:
            log.display_received_date = "Unknown"
            log.excel_received_date = "Unknown"

        # Format Delegation Date
        if log.created_at:
            dt_delegated = localtime(log.created_at) if is_aware(log.created_at) else log.created_at
            log.display_delegation_date = dt_delegated.strftime("%d %b %Y %H:%M:%S")
            log.excel_delegation_date = dt_delegated.strftime("%Y-%m-%d %H:%M:%S")
        else:
            log.display_delegation_date = "Unknown"
            log.excel_delegation_date = "Unknown"
            
        # Map properties to template variables
        log.email_subject = log.subject
        log.live_status = log.status

    # GENERATE XLSX SPREADSHEET IF REQUESTED
    if is_export:
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f'Audit_Logs_{datetime.now().strftime("%Y-%m-%d")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Audit Logs"
        
        # Write Headers (Added 'From Email')
        headers = ['Email Subject', 'From Email', 'Email Received', 'Delegation Date', 'Email Status', 'Delegated Agent']
        ws.append(headers)
        
        # Format Header Row (Bold)
        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True)
            
        # Write Data Rows
        for log in logs:
            ws.append([
                log.email_subject,
                log.from_email,
                log.excel_received_date,
                log.excel_delegation_date,
                log.live_status,
                log.assigned_agent
            ])
            
        wb.save(response)
        return response

    return render(request, 'pssubf/audit_logs.html', {
        'logs': logs,
        'query': query,
        'start_date': start_date_str,
        'end_date': end_date_str
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
    Restores an item from the Recycle Bin back to the Triage Dashboard.
    Updates the delegate status back to 'Assigned' so it returns safely.
    """
    # 1. Get the recycled task record
    task = get_object_or_404(PssubfDelegate, email_id=email_id)
    
    # 2. Update status back to Assigned instead of deleting the row
    task.status = 'Assigned'
    task.assigned_agent = None  # Clear agent so it can be re-assigned cleanly
    task.save()
    
    # 3. Clear inbox status if needed
    inbox_item = PssubfInbox.objects.filter(email_id=email_id).first()
    if inbox_item:
        inbox_item.status = ''
        inbox_item.save()

    # 4. Log the action
    PssubfAction.objects.create(
        task_email_id=email_id,
        action_user=request.user.username,
        action_type="RESTORE",
        note_content="Item restored from Recycle Bin back to Triage Dashboard."
    )
    
    messages.success(request, "Email restored to Dashboard. You can now assign an agent.")
    return redirect('pssubf_dashboard')

logger = logging.getLogger(__name__)
    
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
    """
    Permanently marks a record as permanently deleted ('PERM_DEL') 
    so the dashboard sync loop knows never to recreate it.
    """
    # Instead of hard-deleting which triggers get_or_create on next fetch, 
    # update status to a permanent tombstone state: 'PERM_DEL'
    PssubfDelegate.objects.filter(email_id=email_id).update(status='PERM_DEL', assigned_agent=None)
    PssubfInbox.objects.filter(email_id=email_id).update(status='PERM_DEL')
    
    messages.error(request, "Record permanently deleted from the system.")
    return redirect('pssubf_recycle_bin')


@login_required
def pssubf_bulk_delete(request):
    """
    Handles multiple permanent deletions from the recycle bin 
    by marking them with the 'PERM_DEL' tombstone status so they are never recreated.
    """
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_ids')
        action = request.POST.get('action')

        if selected_ids and action == 'permanent_delete':
            # 🚀 CRITICAL FIX: Update status to 'PERM_DEL' instead of hard-deleting
            # This prevents outlook_dashboard_view sync loop from recreating them via get_or_create.
            PssubfDelegate.objects.filter(email_id__in=selected_ids).update(status='PERM_DEL', assigned_agent=None)
            PssubfInbox.objects.filter(email_id__in=selected_ids).update(status='PERM_DEL')
            
            messages.error(request, f"Permanently deleted {len(selected_ids)} records from the system.")
        else:
            messages.warning(request, "Invalid action or no items selected.")
            
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
    # --- 🟢 1. HANDLE NEW MEMBER POST FROM MODAL ---
    if request.method == 'POST' and request.POST.get('action') == 'add_new_beneficiary':
        membership_number = request.POST.get('membership_number', '').strip()
        
        # Enforce exact 8-digit membership number validation
        if not membership_number or not re.match(r'^\d{8}$', membership_number):
            messages.error(request, "Error: Membership Number is mandatory and must be exactly an 8-digit number.")
            return redirect(request.path)
            
        # Check if membership number already exists in database
        if PssubfBeneficiary.objects.filter(membership_number=membership_number).exists():
            messages.error(request, f"Error: Membership Number '{membership_number}' already exists in the system.")
            return redirect(request.path)

        def clean_dec(val):
            if not val: return 0.00
            try:
                return float(str(val).replace('R', '').replace(' ', '').replace(',', '.'))
            except ValueError:
                return 0.00

        try:
            # 🟢 Safely extract dob and provide a fallback to prevent the 1048 Not Null error
            dob_str = request.POST.get('dob')
            dob_value = dob_str if dob_str else '1900-01-01'

            PssubfBeneficiary.objects.create(
                membership_number=membership_number,
                title=request.POST.get('title', ''),
                initials=request.POST.get('initials', ''),
                first_name=request.POST.get('first_name', ''),
                second_name=request.POST.get('second_name', ''),
                last_name=request.POST.get('last_name', ''),
                id_number=request.POST.get('id_number', ''),
                dob=dob_value,  # 🟢 Added dob field to database insert
                gender=request.POST.get('gender', ''),
                employee_number=request.POST.get('employee_number', ''),
                fund_join_date=request.POST.get('fund_join_date') or None,
                cessation_date=request.POST.get('cessation_date') or None,
                stipened_frequency=request.POST.get('stipened_frequency', ''),
                stipened=clean_dec(request.POST.get('stipened')),
                total_fund_value=clean_dec(request.POST.get('total_fund_value')),
                portfolio_date=request.POST.get('portfolio_date') or None,
                mobile_1=request.POST.get('mobile_1', ''),
                email_1=request.POST.get('email_1', ''),
            )
            messages.success(request, f"Member {membership_number} successfully registered!")
        except Exception as e:
            messages.error(request, f"Database Error: {str(e)}")
            
        # Reload the page to clear the form and display the success message
        return redirect(request.path)


    # --- 🟢 2. STANDARD BENEFICIARY LIST GET LOGIC ---
    # Get all records from the database
    queryset = PssubfBeneficiary.objects.all().order_by('last_name')

    # SEARCH LOGIC (Global database execution)
    search_query = request.GET.get('search')
    if search_query:
        queryset = queryset.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(id_number__icontains=search_query) |
            Q(membership_number__icontains=search_query)  # Added so users can search by membership numbers too
        )

    # Filter Logic (Status based on cessation_date)
    status_filter = request.GET.get('status')
    today = date.today()

    if status_filter == 'expired':
        queryset = queryset.filter(cessation_date__lte=today)
    elif status_filter == 'active':
        queryset = queryset.filter(cessation_date__gt=today)

    # Capture total count before breaking the queryset up via pagination
    total_count = queryset.count()

    # Pagination (36 records per page)
    paginator = Paginator(queryset, 36)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # LIVE CALCULATION: Years, Months, and formatting stipend display if needed
    for member in page_obj:
        if member.dob:
            birth = member.dob
            total_months = (today.year - birth.year) * 12 + (today.month - birth.month)
            if today.day < birth.day:
                total_months -= 1
            total_months = max(0, total_months)
            years = total_months // 12
            months = total_months % 12
            member.calculated_age = f"{years}Y {months:02d}M"
        else:
            member.calculated_age = "N/A"

    # Handle Session Errors (from Excel imports)
    import_errors = request.session.pop('import_errors', [])
    
    return render(request, 'pssubf/beneficiary_list.html', {
        'page_obj': page_obj,
        'import_errors': import_errors,
        'current_status': status_filter,
        'search_query': search_query,
        'total_count': total_count
    })

import os
import requests
from django.core.files.storage import FileSystemStorage

import re

import re

import re

@login_required
def beneficiary_details_view(request, membership_number):
    member = get_object_or_404(PssubfBeneficiary, membership_number=membership_number)
    
    # Pre-define SMS local scope variables to satisfy static analyzers / Pylance
    recipient_number = ""
    sms_reason = ""
    sms_message = ""
    
    # Handles South African formatting (spaces and commas) safely
    def clean_decimal(value):
        if not value or value == '': return 0.00
        cleaned = str(value).replace('R', '').replace(' ', '').replace(',', '.').replace('%', '').strip()
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.00

    if request.method == 'POST':
        action = request.POST.get('action')

        # --- 1. HANDLE DIRECT EMAIL (COMPOSITION TAB) ---
        if action == 'send_direct_email':
            recipient = request.POST.get('to_email')
            cc_email = request.POST.get('cc_email', '').strip()   # 🟢 Added CC support
            bcc_email = request.POST.get('bcc_email', '').strip() # 🟢 Captured BCC
            subject = request.POST.get('subject')
            raw_body_html = request.POST.get('email_html_content')
            
            # Ensure paragraphs format correctly (store raw typed body without manual signature duplication)
            formatted_body = format_email_body(raw_body_html)

            if recipient and subject and formatted_body:
                # Capture any files attached to the direct email form
                uploaded_files = request.FILES.getlist('attachments') 
                if not uploaded_files and request.FILES:
                    uploaded_files = [list(request.FILES.values())[0]]
                
                attachments_payload = []
                file_saved_path = None
                
                for idx, f in enumerate(uploaded_files):
                    content_bytes = f.read()
                    f.seek(0)
                    
                    # Save the first file to local media folder for database referencing
                    if idx == 0:
                        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                        file_saved_path = fs.save(f.name, f)
                        
                    try:
                        encoded_content = base64.b64encode(content_bytes).decode('utf-8')
                        attachments_payload.append({
                            "@odata.type": "#microsoft.graph.fileAttachment",
                            "name": f.name,
                            "contentType": f.content_type,
                            "contentBytes": encoded_content
                        })
                    except Exception as e:
                        logger.error(f"Attachment encoding error: {e}")

                # OutlookGraphService handles the signature automatically when user=request.user is passed
                result = OutlookGraphService.send_outlook_email(
                    sender=settings.OUTLOOK_EMAIL_ADDRESS,
                    recipient=recipient, 
                    cc=cc_email,      # 🟢 Passing CC to Graph Service
                    bcc=bcc_email,    # 🟢 Passing BCC to Graph Service
                    subject=subject, 
                    body=formatted_body,
                    attachments=attachments_payload,
                    user=request.user
                )
                
                if result.get('success') or result == {}:
                    # Only include attachment_path if your PssubfDirectEmail model has the field defined
                    create_kwargs = {
                        'membership_number': membership_number,
                        'agent_name': request.user.username,
                        'recipient': recipient,
                        'subject': subject,
                        'body_html': formatted_body,
                        'sent_at': timezone.now(), # 🟢 FIX: Explicitly setting the direct email timestamp!
                    }
                    if file_saved_path:
                        create_kwargs['attachment_path'] = file_saved_path

                    direct_mail = PssubfDirectEmail.objects.create(**create_kwargs)
                    
                    email_id = f"DIRECT_{membership_number}_{direct_mail.id}"
                    
                    cc_display = f" (CC: {cc_email})" if cc_email else ""
                    bcc_display = f" (BCC: {bcc_email})" if bcc_email else ""
                    
                    PssubfInbox.objects.create(
                        email_id=email_id,
                        subject=subject,
                        sender=settings.OUTLOOK_EMAIL_ADDRESS,
                        snippet=f"Direct Email to {recipient}{cc_display}{bcc_display}",
                        status='Sent',
                        received_timestamp=timezone.now()
                    )

                    PssubfAction.objects.create(
                        task_email_id=email_id,
                        action_type="Direct Email Sent",
                        action_user=request.user.username,
                        note_content=f"Sent to: {recipient} | CC: {cc_email or 'None'} | BCC: {bcc_email or 'None'} | Subject: {subject}",
                        action_timestamp=timezone.now()
                    )
                    messages.success(request, f"Direct email sent successfully to {recipient}.")
                else:
                    messages.error(request, f"Email failed to send: {result.get('error')}")
            return redirect('beneficiary_details', membership_number=membership_number)

        # --- 2. HANDLE GENERAL NOTES (NOTES TAB) ---
        elif action == 'save_note' or 'save_note' in request.POST:
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


        # --- 3A. HANDLE PERSONAL PROFILE UPDATES ---
        elif action == 'update_personal':
            try:
                member.old_membership_number = request.POST.get('old_membership_number', member.old_membership_number)
                member.title = request.POST.get('title', member.title)
                member.initials = request.POST.get('initials', member.initials)
                member.first_name = request.POST.get('first_name', member.first_name)
                member.second_name = request.POST.get('second_name', member.second_name)
                member.last_name = request.POST.get('last_name', member.last_name)
                member.id_number = request.POST.get('id_number', member.id_number)
                
                dob_str = request.POST.get('dob')
                if dob_str:
                    dob_date = datetime.strptime(dob_str, '%Y-%m-%d').date()
                    member.dob = dob_date
                    member.cessation_date = dob_date + relativedelta(years=18)
                
                member.save()

                PssubfAction.objects.create(
                    task_email_id=f"PROFILE_MOD_{membership_number}",
                    action_type="Profile Update",
                    action_user=request.user.username,
                    note_content="Modified beneficiary personal details.",
                    action_timestamp=timezone.now()
                )
                messages.success(request, f"Personal details saved successfully for Member {member.membership_number}.")
            except Exception as e:
                messages.error(request, f"Error updating personal record: {str(e)}")
            return redirect('beneficiary_details', membership_number=member.membership_number)


        # --- 3B. HANDLE FINANCIAL DATA UPDATES ---
        elif action == 'update_profile':
            try:
                member.employee_number = request.POST.get('employee_number', member.employee_number)
                member.stipened_frequency = request.POST.get('stipened_frequency', member.stipened_frequency)
                
                if 'stipened' in request.POST:
                    member.stipened = clean_decimal(request.POST.get('stipened'))
                if 'total_fund_value' in request.POST:
                    member.total_fund_value = clean_decimal(request.POST.get('total_fund_value'))
                
                port_date_str = request.POST.get('portfolio_date')
                if port_date_str:
                    member.portfolio_date = datetime.strptime(port_date_str, '%Y-%m-%d').date()

                join_date_str = request.POST.get('fund_join_date')
                if join_date_str:
                    member.fund_join_date = datetime.strptime(join_date_str, '%Y-%m-%d').date()
                
                member.save()

                PssubfAction.objects.create(
                    task_email_id=f"PROFILE_MOD_{membership_number}",
                    action_type="Fund Update",
                    action_user=request.user.username,
                    note_content="Modified beneficiary financial/fund details.",
                    action_timestamp=timezone.now()
                )
                messages.success(request, f"Financial data saved successfully for Member {member.membership_number}.")
            except Exception as e:
                messages.error(request, f"Error updating financial record: {str(e)}")
            return redirect('beneficiary_details', membership_number=member.membership_number)


        # --- 3C. HANDLE CONTACT CHANNEL UPDATES ---
        elif action == 'update_contact':
            try:
                member.mobile_1 = request.POST.get('mobile_1', member.mobile_1)
                member.email_1 = request.POST.get('email_1', member.email_1)
                member.mobile_2 = request.POST.get('mobile_2', member.mobile_2)
                member.email_2 = request.POST.get('email_2', member.email_2)
                member.mobile_3 = request.POST.get('mobile_3', member.mobile_3)
                member.email_3 = request.POST.get('email_3', member.email_3)
                
                member.save()

                PssubfAction.objects.create(
                    task_email_id=f"PROFILE_MOD_{membership_number}",
                    action_type="Contact Update",
                    action_user=request.user.username,
                    note_content="Modified beneficiary contact channels.",
                    action_timestamp=timezone.now()
                )
                messages.success(request, f"Contact details saved successfully for Member {member.membership_number}.")
            except Exception as e:
                messages.error(request, f"Error updating contact record: {str(e)}")
            return redirect('beneficiary_details', membership_number=member.membership_number)


        # --- 3D. HANDLE GUARDIAN INFO UPDATES ---
        elif action == 'update_guardian':
            try:
                member.guardian_title = request.POST.get('guardian_title', member.guardian_title)
                member.guardian_first_name = request.POST.get('guardian_first_name', member.guardian_first_name)
                member.guardian_last_name = request.POST.get('guardian_last_name', member.guardian_last_name)
                member.guardian_mobile = request.POST.get('guardian_mobile', member.guardian_mobile)
                member.guardian_email = request.POST.get('guardian_email', member.guardian_email)
                member.guardian_address = request.POST.get('guardian_address', member.guardian_address)
                
                member.save()

                PssubfAction.objects.create(
                    task_email_id=f"PROFILE_MOD_{membership_number}",
                    action_type="Guardian Update",
                    action_user=request.user.username,
                    note_content="Modified guardian information.",
                    action_timestamp=timezone.now()
                )
                messages.success(request, f"Guardian information saved successfully for Member {member.membership_number}.")
            except Exception as e:
                messages.error(request, f"Error updating guardian record: {str(e)}")
            return redirect('beneficiary_details', membership_number=member.membership_number)


        # --- 4. HANDLE NEW CLAIM ---
        elif action == 'add_claim_entry':
            try:
                date_logged_str = request.POST.get('date_logged')
                claim_date = datetime.strptime(date_logged_str, '%Y-%m-%d').date() if date_logged_str else date.today()
                
                date_paid_str = request.POST.get('date_paid')
                date_paid_val = datetime.strptime(date_paid_str, '%Y-%m-%d').date() if date_paid_str else None

                calculated_age_str = "---"
                if member.dob:
                    diff_age = relativedelta(claim_date, member.dob)
                    total_m = round((diff_age.years * 12) + diff_age.months + (diff_age.days / 30.44))
                    calculated_age_str = f"{total_m // 12}Y {str(total_m % 12).zfill(2)}M"

                file_payload = request.FILES.get('supporting_document')
                if not file_payload and request.FILES:
                    file_payload = list(request.FILES.values())[0]

                file_status_label = "No"
                file_saved_path = None
                
                if file_payload:
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                    saved_filename = fs.save(file_payload.name, file_payload)
                    file_saved_path = saved_filename
                    file_status_label = "Yes"

                timestamp_string = datetime.now().strftime('%Y%m%d')
                generated_reference = f"CLM-{timestamp_string}{random.randint(1000, 9999)}"

                new_claim = ClaimList.objects.create(
                    beneficiary=member,
                    reference_no=generated_reference,
                    claim_type=request.POST.get('claim_type'),
                    date_logged=claim_date,
                    amount_requested=clean_decimal(request.POST.get('amount_requested')),
                    status=request.POST.get('status', 'Pending'),
                    date_paid=date_paid_val,
                    description=request.POST.get('description'),
                    guardian_name=f"{member.guardian_first_name} {member.guardian_last_name}".strip(),
                    beneficiary_name=f"{member.first_name} {member.last_name}".strip(),
                    beneficiary_dob=member.dob,
                    termination_date=member.cessation_date,
                    portfolio_value=clean_decimal(request.POST.get('portfolio_value', member.total_fund_value)),
                    portfolio_date=request.POST.get('portfolio_date') or member.portfolio_date,
                    age_at_claim=calculated_age_str,
                    supporting_docs_attached=file_status_label,
                    loaded_by_agent=request.user.username,
                    attachment_path=file_saved_path
                )

                ClaimHistory.objects.create(
                    claim_reference=new_claim.reference_no,
                    action_type="Claim Logged",
                    note_content=request.POST.get('description'),
                    attachment_path=file_saved_path,
                    agent_name=request.user.username
                )

                messages.success(request, f"New claim registered successfully. Reference Code: {generated_reference}")
            except Exception as e:
                messages.error(request, f"Claim Error: {str(e)}")
            return redirect('beneficiary_details', membership_number=membership_number)

        # --- 4B. HANDLE UPDATE CLAIM ---
        elif action == 'update_claim_entry':
            try:
                claim_id = request.POST.get('claim_id')
                claim_record = get_object_or_404(ClaimList, id=claim_id)

                date_logged_str = request.POST.get('date_logged')
                if date_logged_str:
                    claim_record.date_logged = datetime.strptime(date_logged_str, '%Y-%m-%d').date()

                date_paid_str = request.POST.get('date_paid')
                claim_record.date_paid = datetime.strptime(date_paid_str, '%Y-%m-%d').date() if date_paid_str else None

                claim_record.claim_type = request.POST.get('claim_type', claim_record.claim_type)
                claim_record.status = request.POST.get('status', claim_record.status)
                claim_record.amount_requested = clean_decimal(request.POST.get('amount_requested'))
                claim_record.description = request.POST.get('description', claim_record.description)

                file_payload = request.FILES.get('supporting_document')
                if file_payload:
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                    saved_filename = fs.save(file_payload.name, file_payload)
                    claim_record.attachment_path = saved_filename
                    claim_record.supporting_docs_attached = "Yes"

                claim_record.save()

                ClaimHistory.objects.create(
                    claim_reference=claim_record.reference_no,
                    action_type="Claim Updated",
                    note_content=f"Updated status to {claim_record.status} and details.",
                    agent_name=request.user.username
                )

                messages.success(request, f"Claim {claim_record.reference_no} updated successfully.")
            except Exception as e:
                messages.error(request, f"Claim Update Error: {str(e)}")
            return redirect('beneficiary_details', membership_number=membership_number)

        # --- 5. HANDLE NEW AD HOC ---
        elif action == 'add_adhoc_entry':
            try:
                claim_date_str = request.POST.get('claim_form_date')
                claim_date = datetime.strptime(claim_date_str, '%Y-%m-%d').date() if claim_date_str else date.today()
                
                years_val = 0.0
                if member.cessation_date and claim_date < member.cessation_date:
                    diff = relativedelta(member.cessation_date, claim_date)
                    total_m = round((diff.years * 12) + diff.months + (diff.days / 30.44))
                    years_val = total_m / 12

                file_payload = request.FILES.get('supporting_document')
                if not file_payload and request.FILES:
                    file_payload = list(request.FILES.values())[0]

                file_status_label = "No"
                file_saved_path = None
                
                if file_payload:
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                    saved_filename = fs.save(file_payload.name, file_payload)
                    file_saved_path = saved_filename
                    file_status_label = "Yes"

                requested_amt = clean_decimal(request.POST.get('amount_requested'))
                portfolio_val = clean_decimal(request.POST.get('portfolio_value', member.total_fund_value))
                stipend_val = float(member.stipened or 0)
                
                total_months = round(years_val * 12)
                calc_liability = total_months * stipend_val
                surplus_calc = portfolio_val - (calc_liability + requested_amt)
                
                afford_string = f"R {surplus_calc:.2f}".strip()[:20]

                AdHocList.objects.create(
                    beneficiary=member,
                    title=request.POST.get('title'),
                    comments=request.POST.get('comments'),
                    claim_form_date=claim_date,
                    status='Pending',
                    supporting_docs_attached=file_status_label,
                    attachment_path=file_saved_path, 
                    years_to_maturity=years_val, 
                    affordability_calculation=afford_string,
                    portfolio_value=portfolio_val,
                    portfolio_date=member.portfolio_date or date.today(),
                    amount_requested=requested_amt
                )
                messages.success(request, "Ad Hoc entry saved successfully.")
            except Exception as e:
                print(traceback.format_exc())
                messages.error(request, f"Ad Hoc Error: {str(e)}")
            return redirect('beneficiary_details', membership_number=membership_number)
            
        # --- 6. HANDLE SEND SMS (WINSMS REST API V1 INTEGRATION & SAFE SQL LOGGING) ---
        elif action == 'send_sms':
            recipient_number = request.POST.get('recipient_number', '').strip()
            sms_reason = request.POST.get('sms_reason', '').strip()
            sms_message = request.POST.get('sms_message', '').strip()

            if not recipient_number or not sms_message:
                return JsonResponse({'status': 'error', 'error': 'Recipient number and message are required.'}, status=400)

            # Strip non-digits and format for South Africa (27...)
            clean_digits = re.sub(r'\D', '', recipient_number)
            if clean_digits.startswith('0'):
                formatted_number = '27' + clean_digits[1:]
            else:
                formatted_number = clean_digits

            api_key = getattr(settings, 'WINSMS_API_KEY', '').strip()

            try:
                # 1. Call WinSMS REST API v1 Endpoint (Raw API Key in AUTHORIZATION header)
                winsms_url = "https://api.winsms.co.za/api/rest/v1/sms/outgoing/send"
                headers = {
                    'AUTHORIZATION': api_key,  # 🟢 RAW API Key passed without Bearer prefix
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                payload = {
                    'message': sms_message,
                    'recipients': [
                        {'mobileNumber': formatted_number}
                    ]
                }

                response = requests.post(winsms_url, json=payload, headers=headers, timeout=15)
                
                # ------------------ WINSMS REST API DEBUG BLOCK ------------------
                #masked_key = f"{api_key[:4]}***" if api_key else "EMPTY"
                #print("\n" + "=" * 60)
                #print(f"[WinSMS REST v1 DEBUG] Destination     : {formatted_number}")
                #print(f"[WinSMS REST v1 DEBUG] HTTP Status Code: {response.status_code}")
                #print(f"[WinSMS REST v1 DEBUG] API Key Loaded  : {masked_key} (Length: {len(api_key)})")
                #print(f"[WinSMS REST v1 DEBUG] Raw JSON Response:\n{response.text}")
                #print("=" * 60 + "\n")
                # -----------------------------------------------------------------

                is_success = False
                error_msg = ""

                if response.status_code in [200, 201]:
                    try:
                        res_json = response.json()
                        recipients_res = res_json.get('recipients', [])
                        if recipients_res and recipients_res[0].get('accepted', False):
                            is_success = True
                            status_label = 'Sent'
                        else:
                            err_detail = recipients_res[0].get('errorDetails', 'Rejected by gateway') if recipients_res else 'No recipient returned'
                            status_label = f"Failed: {err_detail}"
                            error_msg = str(err_detail)
                    except Exception:
                        is_success = True
                        status_label = 'Sent'
                else:
                    try:
                        res_json = response.json()
                        error_msg = res_json.get('errorMessage', res_json.get('message', response.text))
                    except Exception:
                        error_msg = response.text
                    status_label = f"Failed ({response.status_code}): {error_msg}"

                # Safe SQL Truncation to prevent MySQL 1406 "Data too long" exception
                safe_status_label = str(status_label)[:50]

                # 2. Execute raw SQL insert safely
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO sms_logs 
                        (membership_number, recipient_number, reason, message_content, agent_name, status, created_at) 
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, [
                        membership_number,
                        formatted_number,
                        sms_reason,
                        sms_message,
                        request.user.username,
                        safe_status_label
                    ])

                if is_success:
                    return JsonResponse({'status': 'success', 'message': 'SMS sent via WinSMS REST API successfully.'})
                else:
                    return JsonResponse({'status': 'error', 'error': f'WinSMS Gateway Error: {error_msg}'}, status=400)

            except Exception as e:
                logger.error(f"WinSMS Gateway Connection Error: {e}")
                print(f"\n[WinSMS REST DEBUG EXCEPTION] Connection failed: {e}\n")
                
                safe_error_status = f"Failed: Network Error ({str(e)[:25]})"[:50]
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO sms_logs 
                            (membership_number, recipient_number, reason, message_content, agent_name, status, created_at) 
                            VALUES (%s, %s, %s, %s, %s, %s, NOW())
                        """, [
                            membership_number,
                            recipient_number,
                            sms_reason,
                            sms_message,
                            request.user.username,
                            safe_error_status
                        ])
                except Exception as sql_err:
                    logger.error(f"SQL Fallback Logging Error: {sql_err}")

                return JsonResponse({'status': 'error', 'error': f'WinSMS Gateway Connection Error: {str(e)}'}, status=400)

    # --- FETCH DATA FOR TABS ---
    claims = ClaimList.objects.filter(beneficiary__membership_number=membership_number).order_by('-date_logged')
    adhoc_records = AdHocList.objects.filter(beneficiary=member).order_by('-claim_form_date')
    
    recent_logs = SystemLog.objects.all()[:50]

    claim_refs = [c.reference_no for c in claims]
    all_history = ClaimHistory.objects.filter(claim_reference__in=claim_refs).order_by('-created_at')

    # 🟢 UPDATED: Now searches by MIP number OR the Member's ID Number
    incoming_emails = PssubfDelegate.objects.filter(
        Q(member_group_code=membership_number) | 
        Q(id_number=member.id_number) |          # <--- THIS IS THE MAGIC LINK
        Q(email_id__icontains=membership_number)
    ).exclude(email_id__startswith='DIRECT_')
    
    outgoing_emails = PssubfDirectEmail.objects.filter(
        Q(membership_number=membership_number) | 
        Q(membership_number=str(membership_number).strip())
    )

    combined_emails = []
    associated_task_ids = set()

    for e in incoming_emails:
        associated_task_ids.add(e.email_id)
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
            'email_id': f"DIRECT_{membership_number}_{e.id}", 
            'agent': e.agent_name,
            'subject': e.subject,
            'date': e.sent_at,
            'status': 'Sent',
            'type': 'OUTGOING'
        })

    if associated_task_ids:
        replies = PssubfAction.objects.filter(
            task_email_id__in=associated_task_ids, 
            action_type="EMAIL_REPLY"
        )
        for r in replies:
            display_subject = "Reply to Task Request"
            if r.note_content and "Subject: " in r.note_content:
                try:
                    display_subject = r.note_content.split("Subject: ")[1].split("\n")[0]
                except IndexError:  
                    pass

            combined_emails.append({
                'email_id': r.task_email_id,
                'agent': r.action_user,
                'subject': f"RE: {display_subject}",
                'date': r.action_timestamp,
                'status': 'Replied',
                'type': 'OUTGOING'
            })

    combined_emails.sort(key=lambda x: x['date'] if x['date'] else timezone.now(), reverse=True)
    
    internal_notes = PssubfNote.objects.filter(task_email_id__icontains=membership_number).order_by('-created_at')
    pssubf_actions = PssubfAction.objects.filter(Q(task_email_id__icontains=membership_number)).order_by('-action_timestamp')

    for c in claims:
        c.history_logs = [h for h in all_history if h.claim_reference == c.reference_no]
        if member.dob and c.date_logged:
            diff = relativedelta(c.date_logged, member.dob)
            total_m = round((diff.years * 12) + diff.months + (diff.days / 30.44))
            c.age_display = f"{total_m // 12}Y {str(total_m % 12).zfill(2)}M"
        else:
            c.age_display = "---"

    for a in adhoc_records:
        if member.cessation_date and a.claim_form_date:
            diff = relativedelta(member.cessation_date, a.claim_form_date)
            total_m = round((diff.years * 12) + diff.months + (diff.days / 30.44))
            a.maturity_display = f"{total_m // 12}Y {str(total_m % 12).zfill(2)}M"
            stipend_value = float(member.stipened or 0)
            total_liability = total_m * stipend_value
            portfolio_val = float(a.amount_requested or member.total_fund_value or 0)
            surplus_val = portfolio_val - total_liability
            a.calculated_surplus = f"R {surplus_val:,.2f} ({'Surplus' if surplus_val >= 0 else 'Deficit'})"
        else:
            a.maturity_display = "---"
            a.calculated_surplus = "N/A"

    # 🟢 Fetch the SMS Logs from the database
    sms_logs = SmsLog.objects.filter(membership_number=membership_number).order_by('-created_at')

    context = {
        'member': member,
        'claims': claims,
        'adhoc_records': adhoc_records,
        'email_logs': combined_emails,
        'internal_notes': internal_notes,
        'pssubf_actions': pssubf_actions,
        'recent_logs': recent_logs,  
        'sms_logs': sms_logs,            # 🟢 Inject SMS logs into context
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
    """
    API endpoint to auto-populate the New Claim popup.
    Matches your DB Schema: 'stipened' and 'total_fund_value'.
    """
    member = get_object_or_404(PssubfBeneficiary, membership_number=membership_number)
    
    # Calculate current age for the initial view
    today = timezone.now().date()
    age = 0
    if member.dob:
        age = today.year - member.dob.year - ((today.month, today.day) < (member.dob.month, member.dob.day))
    
    data = {
        'success': True,
        'membership_number': member.membership_number,
        'guardian_name': f"{member.guardian_first_name or ''} {member.guardian_last_name or ''}".strip(),
        'beneficiary_name': f"{member.first_name or ''} {member.last_name or ''}".strip(),
        # Date inputs in HTML require YYYY-MM-DD format
        'dob': member.dob.strftime('%Y-%m-%d') if member.dob else '',
        'term_date': member.cessation_date.strftime('%Y-%m-%d') if member.cessation_date else '',
        # Use exact DB column names from your table definition
        'stipened': float(member.stipened or 0),
        'total_fund_value': float(member.total_fund_value or 0),
        'age': age
    }
    return JsonResponse(data)

import io
import os
from django.conf import settings
from django.http import FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from pypdf import PdfReader, PdfWriter

# --- Helper Function for PDF Generation ---
# ReportLab imports for dynamic PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import urllib.request

def generate_excess_claim_pdf(claim):
    output_stream = io.BytesIO()
    
    # 1. Setup Document Dimensions
    doc = SimpleDocTemplate(
        output_stream,
        pagesize=A4,
        rightMargin=1*inch,
        leftMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )

    # 2. Configure Text Styles
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontName = 'Helvetica'
    normal_style.fontSize = 11
    normal_style.leading = 16  
    
    elements = []

    # 3. Add Header Logo via URL
    logo_url = "https://static.futurasa.co.za/images/pssubf-logo.png"
    logo_added = False

    try:
        # Fetch image from URL into memory stream
        req = urllib.request.Request(logo_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            image_data = response.read()
            image_stream = io.BytesIO(image_data)
            
            img = RLImage(image_stream, width=5*inch, height=1.3*inch, kind='proportional')
            img.hAlign = 'LEFT'
            elements.append(img)
            elements.append(Spacer(1, 0.4*inch))
            logo_added = True
    except Exception as e:
        # Fallback if network request fails or URL is unreachable
        pass

    if not logo_added:
        elements.append(Paragraph("<b>Private Security Sector Umbrella Beneficiary Fund</b>", styles['Heading3']))
        elements.append(Spacer(1, 0.4*inch))

    # 4. Extract and Format Database Variables
    current_date = timezone.now().strftime('%d/%m/%Y')
    
    guardian_name = getattr(claim, 'guardian_name', '_________________________')
    beneficiary_name = getattr(claim, 'beneficiary_name', '_________________________')
    
    fund_value_amt = getattr(claim, 'portfolio_value', 0) or 0
    fund_value_str = f"R{float(fund_value_amt):,.2f}"
    
    req_amt = getattr(claim, 'amount_requested', 0) or 0
    amt_requested_str = f"R{float(req_amt):,.2f}"
    
    claim_date = getattr(claim, 'created_at', timezone.now()).strftime('%d/%m/%Y')

    # 5. Build Text Content
    elements.append(Paragraph(f"{current_date}", normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph(f"Guardian: {guardian_name}", normal_style))
    elements.append(Paragraph(f"Beneficiary: {beneficiary_name}", normal_style))
    elements.append(Paragraph(f"Fund value as at {current_date}: {fund_value_str}", normal_style))
    elements.append(Spacer(1, 0.3*inch))
    
    elements.append(Paragraph("Payment request details:", normal_style))
    elements.append(Paragraph(
        f"Ad Hoc payment request submitted on {claim_date} for the total value of<br/>{amt_requested_str}", 
        normal_style
    ))
    elements.append(Spacer(1, 0.3*inch))
    
    ack_text_1 = (
        "I, the guardian of the beneficiary as indicated above, hereby acknowledge that I am "
        "aware that this ad hoc payment will result in a significant reduction in available funds "
        "of the beneficiary's account."
    )
    elements.append(Paragraph(ack_text_1, normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    ack_text_2 = (
        "Further that the funds will not be sufficient to provide for the life expenses of the "
        "beneficiary up to age of majority. Once the funds are depleted, I, the guardian, will be "
        "responsible for any further life expenses of the beneficiary."
    )
    elements.append(Paragraph(ack_text_2, normal_style))
    elements.append(Spacer(1, 0.8*inch))
    
    # 6. Build Signature Block using a Table for structural alignment
    sig_data = [
        ["_________________________________", "_________________________________"],
        ["SIGNATURE of GUARDIAN", "SIGNATURE DATE"]
    ]
    
    sig_table = Table(sig_data, colWidths=[3.2*inch, 3.2*inch])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ]))
    
    elements.append(sig_table)

    # 7. Generate and return the final PDF
    doc.build(elements)
    output_stream.seek(0)
    return output_stream


# --- PDF Download View ---
@login_required
def download_claim_pdf(request, claim_id):
    claim = get_object_or_404(ClaimList, id=claim_id)
    pdf_file = generate_excess_claim_pdf(claim)
    
    response = FileResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Excess_Claim_{claim.reference_no}.pdf"'
    return response

# --- Main Claims View ---
@login_required
def claim_list_view(request):
    """Main view for the full Claim Registry with Dynamic Age Calculation and Filters"""
    
    def clean_numeric(val):
        if not val or str(val).lower() == 'undefined' or str(val).strip() == '':
            return 0
        return float(str(val).replace('R', '').replace(',', '').replace('%', '').strip())

    if request.method == 'POST':
        action = request.POST.get('action')
        m_num = request.POST.get('membership_number')
        
        try:
            member = PssubfBeneficiary.objects.filter(membership_number=m_num).first()
            
            # --- CORRECT FILE STORAGE HANDLING ---
            uploaded_file = request.FILES.get('supporting_document')
            file_saved_path = None
            
            if uploaded_file:
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                saved_filename = fs.save(uploaded_file.name, uploaded_file)
                file_saved_path = saved_filename # Saves properly to disk and gets path

            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
            agent_stamp = f"\n\n--- Managed by {request.user.username} on {timestamp} ---"

            if action == 'add_claim_entry':
                amt_req = clean_numeric(request.POST.get('amount_requested'))
                port_val = clean_numeric(request.POST.get('portfolio_value'))

                new_claim = ClaimList(
                    beneficiary=member,
                    reference_no=f"CLM-{timezone.now().strftime('%Y%m%d%H%M')}",
                    guardian_name=request.POST.get('guardian_name'),
                    beneficiary_name=request.POST.get('beneficiary_name'),
                    beneficiary_dob=request.POST.get('beneficiary_dob') or None,
                    termination_date=request.POST.get('termination_date') or None,
                    claim_type=request.POST.get('claim_type'),
                    description=(request.POST.get('description') or "") + agent_stamp,
                    date_logged=request.POST.get('date_logged') or None,
                    status=request.POST.get('status', 'Created'),
                    portfolio_value=port_val,
                    portfolio_date=request.POST.get('portfolio_date') or None,
                    amount_requested=amt_req,
                    supporting_docs_attached="Yes" if file_saved_path else request.POST.get('supporting_docs_attached'),
                    monthly_income_payment=clean_numeric(request.POST.get('monthly_income')),
                    date_paid=request.POST.get('date_paid') or None,
                    loaded_by_agent=request.user.username,
                    attachment_path=file_saved_path
                )
                new_claim.save()

                # --- INSTANCE LOGGING: CLAIM CREATED ---
                ClaimHistory.objects.create(
                    claim_reference=new_claim.reference_no,
                    action_type="Claim Logged",
                    note_content=request.POST.get('description'),
                    attachment_path=file_saved_path,
                    agent_name=request.user.username
                )

                messages.success(request, f"Claim for Member {m_num} logged.")

            elif action == 'update_claim_entry':
                claim_id = request.POST.get('claim_id')
                claim = get_object_or_404(ClaimList, id=claim_id)
                
                if file_saved_path:
                    claim.attachment_path = file_saved_path
                    claim.supporting_docs_attached = "Yes"
                elif request.POST.get('remove_attachment') == 'true':
                    claim.attachment_path = None
                    claim.supporting_docs_attached = "No"

                claim.guardian_name = request.POST.get('guardian_name')
                claim.beneficiary_name = request.POST.get('beneficiary_name')
                claim.beneficiary_dob = request.POST.get('beneficiary_dob') or None
                claim.termination_date = request.POST.get('termination_date') or None
                claim.date_paid = request.POST.get('date_paid') or None
                claim.claim_type = request.POST.get('claim_type')
                
                new_description_note = request.POST.get('description')
                if new_description_note:
                    claim.description = new_description_note + agent_stamp
                
                claim.date_logged = request.POST.get('date_logged') or None
                claim.status = request.POST.get('status')
                claim.portfolio_value = clean_numeric(request.POST.get('portfolio_value'))
                claim.portfolio_date = request.POST.get('portfolio_date') or None
                claim.amount_requested = clean_numeric(request.POST.get('amount_requested'))
                claim.monthly_income_payment = clean_numeric(request.POST.get('monthly_income'))
                claim.save()

                # --- INSTANCE LOGGING: CLAIM UPDATED ---
                if new_description_note or file_saved_path:
                    ClaimHistory.objects.create(
                        claim_reference=claim.reference_no,
                        action_type="Claim Updated",
                        note_content=new_description_note,
                        attachment_path=file_saved_path,
                        agent_name=request.user.username
                    )

                messages.success(request, f"Claim {claim_id} updated.")

            elif action == 'delete_claim_entry':
                claim_id = request.POST.get('claim_id')
                claim = get_object_or_404(ClaimList, id=claim_id)
                claim_ref = claim.reference_no
                claim.delete()
                messages.success(request, f"Claim {claim_ref} deleted successfully.")

            PssubfAction.objects.create(
                task_email_id=f"CLAIM_{m_num or 'GENERAL'}",
                action_type="Claim Record Managed",
                action_user=request.user.username,
                note_content=f"Action: {action} | Status: {request.POST.get('status', 'N/A')}",
                action_timestamp=timezone.now()
            )
            return redirect('claim_list')
            
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    # Fetching & Filtering Logic
    membership_number = request.GET.get('membership_number')
    status_filter = request.GET.get('status_filter')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    claims = ClaimList.objects.all().select_related('beneficiary').order_by('-date_logged')
    
    if membership_number:
        claims = claims.filter(beneficiary__membership_number__icontains=membership_number)
    
    if status_filter:
        claims = claims.filter(status=status_filter)
        
    if date_from:
        claims = claims.filter(date_logged__gte=date_from)
        
    if date_to:
        claims = claims.filter(date_logged__lte=date_to)

    # DYNAMIC DISPLAY CALCULATION: Age at Claim & Injecting Live Beneficiary Data
    for c in claims:
        if c.beneficiary:
            c.live_beneficiary_name = f"{c.beneficiary.first_name or ''} {c.beneficiary.last_name or ''}".strip()
            c.live_guardian_name = f"{c.beneficiary.guardian_first_name or ''} {c.beneficiary.guardian_last_name or ''}".strip()
        else:
            c.live_beneficiary_name = c.beneficiary_name or "---"
            c.live_guardian_name = c.guardian_name or "---"

        if c.beneficiary and c.beneficiary.dob and c.date_logged:
            diff = relativedelta(c.date_logged, c.beneficiary.dob)
            total_m = round((diff.years * 12) + diff.months + (diff.days / 30.44))
            c.age_display = f"{total_m // 12}Y {str(total_m % 12).zfill(2)}M"
        else:
            c.age_display = "---"

    return render(request, 'claim_list.html', {'claims': claims, 'title': 'Claims Registry'})


from openpyxl.styles import Font, PatternFill, Alignment


def _parse_safe_date(val):
    """Safely converts date, datetime, or mixed date strings into a Python date object."""
    if not val:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    try:
        return date_parser.parse(str(val), dayfirst=True).date()
    except Exception:
        return None


def calculate_adhoc_metrics(beneficiary, claim_form_date, portfolio_value, amount_requested):
    """
    Calculates Age at Claim Date (decimal years), Years to Maturity (decimal years),
    Maturity Display ('4Y 11M'), Total Months, and Affordability Result using the
    exact Snippet 1 formula: P - (MONTHS * S + R).
    """
    dob = _parse_safe_date(beneficiary.dob) if beneficiary else None
    term_date = _parse_safe_date(beneficiary.cessation_date) if beneficiary else None
    claim_date = _parse_safe_date(claim_form_date)

    # Column E: Age at Claim Date (decimal years, e.g. 13.51)
    age_decimal = 0.0
    if dob and claim_date:
        age_decimal = round((claim_date - dob).days / 365.25, 2)

    # Column G: Years to Maturity (decimal years) & Snippet 1 totalMonths
    years_to_maturity_decimal = 0.0
    total_months = 0
    maturity_display = "---"
    if term_date and claim_date:
        if term_date > claim_date:
            years_to_maturity_decimal = round((term_date - claim_date).days / 365.25, 2)
            diff = relativedelta(term_date, claim_date)
            total_months_precise = (diff.years * 12) + diff.months + (diff.days / 30.44)
            final_y = int(total_months_precise // 12)
            final_m = round(total_months_precise % 12)
            if final_m == 12:
                final_y += 1
                final_m = 0
            total_months = (final_y * 12) + final_m
            maturity_display = f"{final_y}Y {final_m:02d}M"
        else:
            years_to_maturity_decimal = 0.0
            total_months = 0
            maturity_display = "0Y 00M"

    # Column O: Affordability Result = P - (MONTHS * S + R)
    p_val = float(portfolio_value or 0)
    r_val = float(amount_requested or 0)
    s_val = float(beneficiary.stipened or 0) if beneficiary else 0.0
    affordability_num = round(p_val - ((total_months * s_val) + r_val), 2)

    return {
        'age_decimal': age_decimal,
        'years_to_maturity': years_to_maturity_decimal,
        'total_months': total_months,
        'maturity_display': maturity_display,
        'affordability_num': affordability_num,
    }


def _filter_adhoc_records(request):
    """Applies Membership No. and Claim Form Date range filters consistently for view & export."""
    membership_number = request.GET.get('membership_number', '').strip()
    date_from_str = request.GET.get('date_from', '').strip()
    date_to_str = request.GET.get('date_to', '').strip()

    adhoc_records = AdHocList.objects.all().select_related('beneficiary').order_by('-date_created')

    if membership_number:
        adhoc_records = adhoc_records.filter(beneficiary__membership_number__icontains=membership_number)

    if date_from_str or date_to_str:
        parsed_from = None
        parsed_to = None
        try:
            if date_from_str:
                parsed_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            if date_to_str:
                parsed_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            pass

        filtered_list = []
        for a in adhoc_records:
            record_date = _parse_safe_date(a.claim_form_date)
            if not record_date:
                continue
            if parsed_from and record_date < parsed_from:
                continue
            if parsed_to and record_date > parsed_to:
                continue
            filtered_list.append(a)
        adhoc_records = filtered_list

    return adhoc_records, membership_number, date_from_str, date_to_str


@login_required
def ad_hoc_list_view(request):
    """Main view for the Ad Hoc Registry with Dynamic Maturity, DB Affordability Commit & Excel Export."""

    def clean_float(val):
        if not val or str(val).lower() == 'undefined' or str(val).strip() == '':
            return 0.0
        try:
            return float(str(val).replace('R', '').replace(',', '').replace('%', '').strip())
        except ValueError:
            return 0.0

    if request.method == 'POST':
        action = request.POST.get('action')
        m_num = request.POST.get('membership_number')

        try:
            if action == 'delete_adhoc_entry':
                record_id = request.POST.get('record_id')
                record = get_object_or_404(AdHocList, id=record_id)
                record.delete()
                messages.success(request, f"Ad Hoc Record {record_id} deleted successfully.")
                return redirect('adhoc_list')

            member = get_object_or_404(PssubfBeneficiary, membership_number=m_num)
            uploaded_file = request.FILES.get('supporting_document')
            file_saved_path = None
            if uploaded_file:
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT))
                file_saved_path = fs.save(uploaded_file.name, uploaded_file)

            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
            agent_stamp = f"\n\n--- Managed by {request.user.username} on {timestamp} ---"

            claim_form_date = request.POST.get('claim_form_date') or None
            portfolio_val = clean_float(request.POST.get('portfolio_value'))
            requested_amt = clean_float(request.POST.get('amount_requested'))

            # Compute exact Snippet 1 metrics to commit to the DB
            metrics = calculate_adhoc_metrics(member, claim_form_date, portfolio_val, requested_amt)

            if action == 'add_adhoc_entry':
                AdHocList.objects.create(
                    beneficiary=member,
                    title=request.POST.get('title'),
                    comments=(request.POST.get('comments') or "") + agent_stamp,
                    claim_form_date=claim_form_date,
                    date_paid=request.POST.get('date_paid') or None,
                    status=request.POST.get('status', 'Created'),
                    supporting_docs_attached=request.POST.get('supporting_docs_attached', 'No'),
                    attachment_path=file_saved_path,
                    portfolio_value=portfolio_val,
                    portfolio_date=request.POST.get('portfolio_date') or None,
                    amount_requested=requested_amt,
                    years_to_maturity=metrics['years_to_maturity'],
                    affordability_calculation=f"{metrics['affordability_num']:.2f}",
                )
                messages.success(request, f"New Ad Hoc claim for Member {m_num} successfully logged.")

            elif action == 'update_adhoc_entry':
                record_id = request.POST.get('record_id')
                record = get_object_or_404(AdHocList, id=record_id)

                if file_saved_path:
                    record.attachment_path = file_saved_path
                elif request.POST.get('remove_attachment') == 'true':
                    record.attachment_path = None

                record.beneficiary = member
                record.title = request.POST.get('title')
                record.status = request.POST.get('status')
                record.claim_form_date = claim_form_date
                record.date_paid = request.POST.get('date_paid') or None
                record.supporting_docs_attached = request.POST.get('supporting_docs_attached')
                record.portfolio_value = portfolio_val
                record.portfolio_date = request.POST.get('portfolio_date') or None
                record.amount_requested = requested_amt
                record.years_to_maturity = metrics['years_to_maturity']
                record.affordability_calculation = f"{metrics['affordability_num']:.2f}"

                user_comments = request.POST.get('comments') or ""
                if agent_stamp not in (record.comments or ""):
                    record.comments = user_comments + agent_stamp
                else:
                    record.comments = user_comments

                record.save()
                messages.success(request, f"Ad Hoc Record {record_id} has been updated.")

            return redirect('adhoc_list')

        except Exception as e:
            logger.error(f"Ad Hoc Process Error: {e}", exc_info=True)
            messages.error(request, f"Process Error: {str(e)}")

    # Redirect any ?export=... query straight to the Excel exporter
    if request.GET.get('export') in ('excel', 'xlsx', 'csv'):
        return export_adhoc_excel(request)

    adhoc_records, membership_number, date_from_str, date_to_str = _filter_adhoc_records(request)

    for a in adhoc_records:
        metrics = calculate_adhoc_metrics(a.beneficiary, a.claim_form_date, a.portfolio_value, a.amount_requested)
        a.maturity_display = metrics['maturity_display']

    context = {
        'adhoc_list': adhoc_records,
        'title': 'Ad Hoc Registry',
        'current_member': membership_number,
        'date_from': date_from_str,
        'date_to': date_to_str,
    }
    return render(request, 'Ad_hoc_list.html', context)


@login_required
def export_adhoc_excel(request):
    """
    Exports the filtered Ad Hoc Registry to Excel matching the exact 17-column
    (A through Q) template: Ad-Hoc claim listing.
    """
    records, membership_number, date_from_str, date_to_str = _filter_adhoc_records(request)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Ad_Hoc_List_{timezone.now().strftime('%Y-%m-%d %H_%M_%S')}"[:31]

    headers = [
        'A - Member Number',
        'B - Guardian Name & Surname',
        'C - Beneficiary Name & Surname',
        'D - Beneficiary Date Of Birth',
        'E - Age at Claim Date',
        'F - Termination Date',
        'G - Years to Maturity',
        'H - Original Claim Form Date',
        'I - Portfolio Value',
        'J - Portfolio Value Date',
        'K - Monthly Income Payment',
        'L - Amount Requested',
        'M - Reason',
        'N - Supporting Documents Attached',
        'O - Affordability Calc',
        'P - Note',
        'Status',
    ]
    ws.append(headers)

    header_font = Font(name='Aptos Narrow', size=11, bold=True, color='000000')
    for cell in ws[1]:
        cell.font = header_font
        cell.alignment = Alignment(horizontal='left', vertical='center')

    for rec in records:
        b = rec.beneficiary
        metrics = calculate_adhoc_metrics(b, rec.claim_form_date, rec.portfolio_value, rec.amount_requested)

        # Keep DB in sync if historic record was missing the saved calculation
        formatted_calc = f"{metrics['affordability_num']:.2f}"
        if rec.affordability_calculation != formatted_calc or float(rec.years_to_maturity or 0) != metrics['years_to_maturity']:
            AdHocList.objects.filter(id=rec.id).update(
                years_to_maturity=metrics['years_to_maturity'],
                affordability_calculation=formatted_calc,
            )

        member_num = b.membership_number if b else ''
        if str(member_num).isdigit():
            member_num = int(member_num)

        guardian_name = f"{b.guardian_first_name or ''} {b.guardian_last_name or ''}".strip() if b else ''
        beneficiary_name = f"{b.first_name or ''} {b.last_name or ''}".strip() if b else ''
        dob_val = _parse_safe_date(b.dob) if b else None
        term_val = _parse_safe_date(b.cessation_date) if b else None
        claim_date_val = _parse_safe_date(rec.claim_form_date)
        port_date_val = _parse_safe_date(rec.portfolio_date)

        # Strip system tracking stamps so Column P only shows the manual note
        clean_note = rec.comments.split('--- Managed by')[0].strip() if rec.comments else ''
        clean_note = clean_note if clean_note else None

        row_data = [
            member_num,                          # A - Member Number
            guardian_name,                       # B - Guardian Name & Surname
            beneficiary_name,                    # C - Beneficiary Name & Surname
            dob_val,                             # D - Beneficiary Date Of Birth
            metrics['age_decimal'],              # E - Age at Claim Date
            term_val,                            # F - Termination Date
            metrics['years_to_maturity'],        # G - Years to Maturity
            claim_date_val,                      # H - Original Claim Form Date
            float(rec.portfolio_value or 0),     # I - Portfolio Value
            port_date_val,                       # J - Portfolio Value Date
            float(b.stipened or 0) if b else 0,  # K - Monthly Income Payment
            float(rec.amount_requested or 0),    # L - Amount Requested
            rec.title or '',                     # M - Reason
            rec.supporting_docs_attached or '',  # N - Supporting Documents Attached
            metrics['affordability_num'],        # O - Affordability Calc (Snippet 1 formula)
            clean_note,                          # P - Note
            rec.status or '',                    # Q - Status
        ]
        ws.append(row_data)

        # Apply clean date & numeric formats to the newly added row
        r_idx = ws.max_row
        for col_idx in (4, 6, 8, 10):  # D, F, H, J dates
            if ws.cell(r_idx, col_idx).value:
                ws.cell(r_idx, col_idx).number_format = 'yyyy-mm-dd'
        for col_idx in (9, 11, 12, 15):  # I, K, L, O currency/numeric values
            ws.cell(r_idx, col_idx).number_format = '#,##0.00'

    # Auto-fit column widths
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value is not None:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 13), 45)

    # Dynamic filename matching your example format
    if date_from_str and date_to_str:
        f_from = _parse_safe_date(date_from_str)
        f_to = _parse_safe_date(date_to_str)
        if f_from and f_to:
            filename = f"Ad-Hoc claim listing {f_from.strftime('%d.%m.%Y')} to {f_to.strftime('%d.%m.%Y')}.xlsx"
        else:
            filename = f"Ad-Hoc claim listing {date.today().strftime('%d.%m.%Y')}.xlsx"
    else:
        filename = f"Ad-Hoc claim listing {date.today().strftime('%d.%m.%Y')}.xlsx"

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@login_required
def get_adhoc_details_view(request, record_id):
    """API endpoint to fetch Ad Hoc record details including live updated beneficiary information."""
    try:
        record = get_object_or_404(AdHocList, id=record_id)
        beneficiary = record.beneficiary

        guardian_name = ""
        beneficiary_name = ""
        dob = ""
        termination_date = ""
        stipened = 0  # Default to 0
        
        if beneficiary:
            guardian_name = f"{beneficiary.guardian_first_name or ''} {beneficiary.guardian_last_name or ''}".strip()
            beneficiary_name = f"{beneficiary.first_name or ''} {beneficiary.last_name or ''}".strip()
            dob = beneficiary.dob.strftime('%Y-%m-%d') if beneficiary.dob else ''
            
            # Matches claims logic exactly
            if beneficiary.cessation_date:
                termination_date = beneficiary.cessation_date.strftime('%Y-%m-%d')
                
            # Matches claims logic exactly - simple float cast
            if beneficiary.stipened:
                stipened = float(beneficiary.stipened)

        data = {
            'success': True,
            'membership_number': beneficiary.membership_number if beneficiary else '',
            'guardian_name': guardian_name, 
            'beneficiary_name': beneficiary_name, 
            'dob': dob,
            'termination_date': termination_date,
            'stipened': stipened,  # 🟢 Safe native float, perfectly matching JS expected key
            'title': record.title,
            'status': record.status,
            'claim_form_date': record.claim_form_date.strftime('%Y-%m-%d') if record.claim_form_date else '',
            'date_paid': record.date_paid.strftime('%Y-%m-%d') if record.date_paid else '',
            'supporting_docs_attached': record.supporting_docs_attached,
            'portfolio_value': float(record.portfolio_value or 0),
            'portfolio_date': record.portfolio_date.strftime('%Y-%m-%d') if record.portfolio_date else '',
            'amount_requested': float(record.amount_requested or 0),
            'comments': record.comments,
            'attachment_path': record.attachment_path.name if hasattr(record.attachment_path, 'name') else str(record.attachment_path) if record.attachment_path else None
        }
        return JsonResponse(data)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def download_adhoc_attachment(request, record_id):
    """Securely downloads the Ad Hoc attachment and handles missing files gracefully."""
    record = get_object_or_404(AdHocList, id=record_id)
    
    if not record.attachment_path:
        messages.error(request, "No attachment is linked to this record.")
        return redirect('adhoc_list')
        
    # Build the physical path to the file
    file_path = os.path.join(settings.MEDIA_ROOT, str(record.attachment_path))
    
    # Check if the file actually exists on the hard drive
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        # Force download instead of opening in browser
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response
    else:
        # Prevents the ugly 404 page if an old test file is missing
        messages.error(request, f"The physical file '{record.attachment_path}' is missing from the server.")
        return redirect('adhoc_list')

@login_required
def get_claim_details(request, claim_id):
    """Fetches full claim data, pulling live updated beneficiary and guardian information."""
    claim = get_object_or_404(ClaimList, id=claim_id)
    member = claim.beneficiary
    
    # Clean the description so the agent doesn't edit the old tracking stamps
    clean_description = claim.description or ""
    if "--- Managed by" in clean_description:
        clean_description = clean_description.split("---")[0].strip()

    # Pull live values from the linked PssubfBeneficiary record if available, 
    # falling back to frozen claim column data if necessary.
    guardian_name = ""
    beneficiary_name = ""
    dob = ""
    term_date = ""
    monthly_income = float(claim.monthly_income_payment or 0)
    portfolio_value = float(claim.portfolio_value or 0)

    if member:
        guardian_name = f"{member.guardian_first_name or ''} {member.guardian_last_name or ''}".strip()
        beneficiary_name = f"{member.first_name or ''} {member.last_name or ''}".strip()
        dob = member.dob.strftime('%Y-%m-%d') if member.dob else ''
        term_date = member.cessation_date.strftime('%Y-%m-%d') if member.cessation_date else ''
        if member.stipened:
            monthly_income = float(member.stipened)
        if member.total_fund_value:
            portfolio_value = float(member.total_fund_value)
    else:
        guardian_name = claim.guardian_name or ""
        beneficiary_name = claim.beneficiary_name or ""
        dob = claim.beneficiary_dob.strftime('%Y-%m-%d') if claim.beneficiary_dob else ''
        term_date = claim.termination_date.strftime('%Y-%m-%d') if claim.termination_date else ''

    data = {
        'membership_number': member.membership_number if member else '',
        'guardian_name': guardian_name, # 🔴 Returns live updated guardian name
        'beneficiary_name': beneficiary_name, # 🔴 Returns live updated beneficiary name
        'dob': dob,
        'term_date': term_date,
        'claim_type': claim.claim_type,
        'age_at_claim': claim.age_at_claim,
        'monthly_income': monthly_income,
        'date_logged': claim.date_logged.strftime('%Y-%m-%d') if claim.date_logged else '',
        'portfolio_value': portfolio_value,
        'portfolio_date': claim.portfolio_date.strftime('%Y-%m-%d') if claim.portfolio_date else '',
        'amount_requested': float(claim.amount_requested or 0),
        'status': claim.status,
        'date_paid': claim.date_paid.strftime('%Y-%m-%d') if hasattr(claim, 'date_paid') and claim.date_paid else '',
        'description': clean_description,
        'docs_attached': claim.supporting_docs_attached
    }
    return JsonResponse(data)


def _filter_claims_records(request):
    """Applies Membership No., Status, and Claim Date range filters consistently for view & export."""
    membership_number = request.GET.get('membership_number', '').strip()
    status_filter = request.GET.get('status_filter', '').strip()
    date_from_str = request.GET.get('date_from', '').strip()
    date_to_str = request.GET.get('date_to', '').strip()

    claims = ClaimList.objects.all().select_related('beneficiary').order_by('-date_logged')

    if membership_number:
        claims = claims.filter(beneficiary__membership_number__icontains=membership_number)

    if status_filter:
        claims = claims.filter(status=status_filter)

    if date_from_str:
        claims = claims.filter(date_logged__gte=date_from_str)

    if date_to_str:
        claims = claims.filter(date_logged__lte=date_to_str)

    return claims, membership_number, status_filter, date_from_str, date_to_str


@login_required
def export_claims_excel(request):
    """
    Exports the filtered Claim Registry (ClaimList model) to Excel matching
    the exact 14-column (A through N) template: Claim listing.
    """
    records, membership_number, status_filter, date_from_str, date_to_str = _filter_claims_records(request)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Claims_List_{timezone.now().strftime('%Y-%m-%d %H_%M_%S')}"[:31]

    headers = [
        'A - Member Number',
        'B - Guardian Name & Surname',
        'C - Beneficiary Name & Surname',
        'D - Beneficiary Date Of Birth',
        'E - Age at Claim Date',
        'F - Termination Date',
        'G - Original Claim Form Date',
        'H - Portfolio Value',
        'I - Portfolio Value Date',
        'J - Monthly Income Payment',
        'K - Amount Requested',
        'L - Reason',
        'M - Supporting Documents Attached',
        'Status',
    ]
    ws.append(headers)

    header_font = Font(name='Aptos Narrow', size=11, bold=True, color='000000')
    for cell in ws[1]:
        cell.font = header_font
        cell.alignment = Alignment(horizontal='left', vertical='center')

    for rec in records:
        b = rec.beneficiary

        # Member number (numeric if purely digits, matching template)
        member_num = b.membership_number if b else (rec.beneficiary_id or '')
        if str(member_num).isdigit():
            member_num = int(member_num)

        # Live beneficiary details with fallback to stored claim snapshot
        if b:
            guardian = f"{b.guardian_first_name or ''} {b.guardian_last_name or ''}".strip()
            beneficiary_full_name = f"{b.first_name or ''} {b.last_name or ''}".strip()
            dob_val = _parse_safe_date(b.dob)
            term_val = _parse_safe_date(b.cessation_date)
        else:
            guardian = rec.guardian_name or ''
            beneficiary_full_name = rec.beneficiary_name or ''
            dob_val = _parse_safe_date(rec.beneficiary_dob)
            term_val = _parse_safe_date(rec.termination_date)

        claim_date_val = _parse_safe_date(rec.date_logged)
        port_date_val = _parse_safe_date(rec.portfolio_date)

        # Column E: Exact decimal Age at Claim Date (e.g. 18.99)
        age_decimal = 0.0
        if dob_val and claim_date_val:
            age_decimal = round((claim_date_val - dob_val).days / 365.25, 2)

        monthly_income = float(rec.monthly_income_payment or 0)
        if monthly_income == 0 and b and b.stipened:
            monthly_income = float(b.stipened)

        row_data = [
            member_num,                          # A - Member Number
            guardian,                            # B - Guardian Name & Surname
            beneficiary_full_name,               # C - Beneficiary Name & Surname
            dob_val,                             # D - Beneficiary Date Of Birth
            age_decimal,                         # E - Age at Claim Date
            term_val,                            # F - Termination Date
            claim_date_val,                      # G - Original Claim Form Date
            float(rec.portfolio_value or 0),     # H - Portfolio Value
            port_date_val,                       # I - Portfolio Value Date
            monthly_income,                      # J - Monthly Income Payment
            float(rec.amount_requested or 0),    # K - Amount Requested
            rec.claim_type or '',                # L - Reason
            rec.supporting_docs_attached or '',  # M - Supporting Documents Attached
            rec.status or '',                    # N - Status
        ]
        ws.append(row_data)

        # Apply clean date & currency formats
        r_idx = ws.max_row
        for col_idx in (4, 6, 7, 9):  # D, F, G, I dates
            if ws.cell(r_idx, col_idx).value:
                ws.cell(r_idx, col_idx).number_format = 'yyyy-mm-dd'
        for col_idx in (8, 10, 11):  # H, J, K currency/numeric values
            ws.cell(r_idx, col_idx).number_format = '#,##0.00'

    # Auto-fit column widths
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value is not None:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 13), 45)

    # Dynamic filename matching your example format
    if date_from_str and date_to_str:
        f_from = _parse_safe_date(date_from_str)
        f_to = _parse_safe_date(date_to_str)
        if f_from and f_to:
            filename = f"Claim listing {f_from.strftime('%d.%m.%Y')} to {f_to.strftime('%d.%m.%Y')}.xlsx"
        else:
            filename = f"Claim listing {date.today().strftime('%d.%m.%Y')}.xlsx"
    else:
        filename = f"Claim listing {date.today().strftime('%d.%m.%Y')}.xlsx"

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response

from dateutil.relativedelta import relativedelta

@login_required
def affordability_dashboard(request):
    """View the calculator and history"""
    results = ClaimAffordability.objects.all().order_by('-calculated_at')
    return render(request, 'affordability_dashboard.html', {'results': results})

from django.db.models import Sum

@login_required
def run_manual_calc(request):
    if request.method == 'POST':
        m_num = request.POST.get('membership_number')
        member = get_object_or_404(PssubfBeneficiary, membership_number=m_num)
        
        # Use the stored fund value from the database
        fund_val = float(member.total_fund_value or 0)
        stipend = float(member.stipened or 0)
        
        if member.dob:
            today = date.today()
            majority_date = member.dob + relativedelta(years=18)
            
            # Calculate months remaining
            if majority_date <= today:
                total_months = 0
            else:
                diff = relativedelta(majority_date, today)
                total_months = (diff.years * 12) + diff.months

            # CORE MATH: Only Stipends
            total_stipend_commitment = stipend * total_months
            
            # Final Balance is Fund minus what we OWE in stipends
            final_bal = fund_val - total_stipend_commitment

            ClaimAffordability.objects.update_or_create(
                membership_number=m_num,
                defaults={
                    'majority_date': majority_date,
                    'years_to_majority': round(total_months / 12, 2),
                    'months_to_majority': total_months,
                    'total_stipend_commitment': total_stipend_commitment,
                    'fund_after_stipend': final_bal, 
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

import openpyxl
from datetime import date
from django.db.models import Q, Count
from django.utils.dateparse import parse_date
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from openpyxl.styles import Font, PatternFill, Alignment
# 🚀 FIX: Imported PssubfDirectEmail instead of DirectEmailLog
from .models import ClaimList, PssubfAction, PssubfBeneficiary, PssubfDirectEmail

@login_required
def claim_sla_report_view(request):
    if request.user.username.lower() not in ['omega', 'manager']:
        return redirect('dashboard')

    start_str = request.GET.get('start_date')
    end_str = request.GET.get('end_date')
    
    def get_valid_date(date_val):
        if date_val and date_val != "None" and date_val != "":
            return parse_date(date_val)
        return None

    # 1. Setup Filters
    claims_q = Q()
    actions_q = Q()
    emails_q = Q()

    start_dt = get_valid_date(start_str)
    if start_dt:
        claims_q &= Q(date_logged__gte=start_dt)
        actions_q &= Q(action_timestamp__date__gte=start_dt)
        emails_q &= Q(sent_at__date__gte=start_dt)

    end_dt = get_valid_date(end_str)
    if end_dt:
        claims_q &= Q(date_logged__lte=end_dt)
        actions_q &= Q(action_timestamp__date__lte=end_dt)
        emails_q &= Q(sent_at__date__lte=end_dt)

    # 2. Handle Excel Export
    if request.GET.get('export') == 'excel':
        return export_claims_sla_excel(claims_q, actions_q, emails_q)

    # 3. Aggregate Data for Dashboard
    type_breakdown = ClaimList.objects.filter(claims_q).values('claim_type', 'status').annotate(total=Count('id')).order_by('claim_type')
    action_breakdown = PssubfAction.objects.filter(actions_q).values('action_type', 'action_user').annotate(total=Count('id')).order_by('action_type')
    
    # 🚀 FIX: Using agent_name instead of sent_by_user
    email_breakdown = PssubfDirectEmail.objects.filter(emails_q).values(
        'subject', 'agent_name'
    ).annotate(total=Count('id')).order_by('-total')

    report_data = {
        'TYPES': type_breakdown,
        'TYPES_TOTAL': sum(item['total'] for item in type_breakdown),
        
        'ACTIONS': action_breakdown,
        'ACTIONS_TOTAL': sum(item['total'] for item in action_breakdown),
        
        'SENT_EMAILS': email_breakdown,
        'SENT_TOTAL': sum(item['total'] for item in email_breakdown),
    }

    grand_total = report_data['TYPES_TOTAL'] + report_data['ACTIONS_TOTAL'] + report_data['SENT_TOTAL']
    recent_details = ClaimList.objects.filter(claims_q).order_by('-date_logged')[:50]

    context = {
        'report': report_data,
        'grand_total': grand_total,
        'start_date': start_str,
        'end_date': end_str,
        'details': recent_details,
        'title': 'SLA Performance Report'
    }
    return render(request, 'claim_sla_report.html', context)

def export_claims_sla_excel(claims_q, actions_q, emails_q):
    wb = openpyxl.Workbook()
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1B5E20", end_color="1B5E20", fill_type="solid")
    
    def clean_date(dt):
        if dt:
            try:
                return dt.replace(tzinfo=None)
            except AttributeError:
                return dt 
        return "N/A"

    # --- SHEET 1: CLAIMS LOG ---
    ws1 = wb.active
    ws1.title = "Claims Audit Trail"
    headers = ['Reference', 'Member No', 'Beneficiary', 'Claim Type', 'Date Logged', 'Status', 'Agent', 'Portfolio Value']
    ws1.append(headers)
    for cell in ws1[1]:
        cell.font, cell.fill, cell.alignment = header_font, header_fill, Alignment(horizontal="center")

    for c in ClaimList.objects.filter(claims_q).order_by('-date_logged'):
        ws1.append([c.reference_no, c.beneficiary_id, c.beneficiary_name, c.claim_type, c.date_logged, c.status, c.loaded_by_agent, float(c.portfolio_value or 0)])

    # --- SHEET 2: AGENT ACTIVITY ---
    ws2 = wb.create_sheet(title="Agent Performance")
    ws2.append(['Timestamp', 'Agent', 'Action', 'Target Record', 'Notes'])
    for cell in ws2[1]:
        cell.font, cell.fill, cell.alignment = header_font, header_fill, Alignment(horizontal="center")

    for a in PssubfAction.objects.filter(actions_q).order_by('-action_timestamp'):
        ws2.append([clean_date(a.action_timestamp), a.action_user, a.action_type, a.task_email_id, a.note_content])

    # --- SHEET 3: EMAIL LOGS ---
    ws3 = wb.create_sheet(title="Correspondence Log")
    ws3.append(['Sent At', 'User', 'Recipient', 'Subject', 'Member No'])
    for cell in ws3[1]:
        cell.font, cell.fill, cell.alignment = header_font, header_fill, Alignment(horizontal="center")

    # 🚀 FIX: Using PssubfDirectEmail and correct field names (agent_name, recipient)
    for e in PssubfDirectEmail.objects.filter(emails_q).order_by('-sent_at'):
        ws3.append([
            clean_date(e.sent_at), 
            e.agent_name, 
            e.recipient, 
            e.subject, 
            e.membership_number
        ])

    for sheet in [ws1, ws2, ws3]:
        for col in sheet.columns:
            sheet.column_dimensions[col[0].column_letter].width = 25

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="PSSUBF_SLA_{date.today()}.xlsx"'
    wb.save(response)
    return response

from django.template.loader import render_to_string

def get_user_email_signature(user):
    """
    Maps system usernames to Full Names and renders the email signature template.
    """
    username = user.username if hasattr(user, 'username') else str(user)
    
    # Map your system usernames to the full name that should display in the signature
    name_mapping = {
        'LuanovanEck': 'Luano van Eck',
        'Testuser1': 'Test Agent',
        'omega': 'Omega System Assistant',
        'Chris-Nicolla': 'Chris Nicolla',
        'Athena': 'Athena',
        'Vanessa': 'Vanessa'
    }
    
    # Fallback to the username or title-case if not explicitly mapped
    full_name = name_mapping.get(username, username.replace('_', ' ').title())
    
    context = {
        'agent_full_name': full_name,
        'username': username,
    }
    
    # Renders your signature template located at pssubf/pssubf_email_signature.html
    try:
        signature_html = render_to_string('pssubf/pssubf_email_signature.html', context)
    except Exception:
        # Fallback inline signature if template path ever changes
        signature_html = f"<br><br><p>Kind regards,<br><strong>{full_name}</strong><br>PSSUBF Administrator</p>"
        
    return signature_html



@login_required
def sms_list_view(request):
    query = request.GET.get('q', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    export_action = request.GET.get('export', '').strip()

    # Base queryset
    sms_logs = SmsLog.objects.all().order_by('-created_at')


    # 1. Universal Search (searches membership, recipient, agent, reason, message content, status)
    if query:
        sms_logs = sms_logs.filter(
            Q(membership_number__icontains=query) | 
            Q(recipient_number__icontains=query) |
            Q(agent_name__icontains=query) |
            Q(reason__icontains=query) |
            Q(message_content__icontains=query) |
            Q(status__icontains=query)
        )

    # 2. Date Range Filtering
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, '%Y-%m-%d')
            sms_logs = sms_logs.filter(created_at__gte=dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            # Include the full end day up to 23:59:59
            dt_to = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            sms_logs = sms_logs.filter(created_at__lte=dt_to)
        except ValueError:
            pass

    # 3. Handle CSV Export
    if export_action == 'csv':
        response = HttpResponse(content_type='text/csv')
        filename_date = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="sms_audit_logs_{filename_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Date Sent', 'Membership Number', 'Agent', 'Recipient Number', 'Reason / Template', 'Message Content', 'Status'])
        
        for sms in sms_logs:
            writer.writerow([
                sms.id,
                sms.created_at.strftime('%Y-%m-%d %H:%M:%S') if sms.created_at else '',
                sms.membership_number,
                sms.agent_name or 'System',
                sms.recipient_number,
                sms.reason or 'Manual Custom Message',
                sms.message_content,
                sms.status
            ])
        return response

    # Limit standard list view rendering to avoid browser overload if unbound
    sms_logs_limited = sms_logs[:500]

    context = {
        'sms_logs': sms_logs_limited,
        'total_count': sms_logs.count(),
        'title': 'Global SMS Logs'
    }
    return render(request, 'pssubf/sms_list.html', context)