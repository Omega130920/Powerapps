from base64 import urlsafe_b64decode, urlsafe_b64encode
import base64
from collections import defaultdict
import csv
from functools import cache
import io
import json
import mimetypes
import os
import pickle
import time
from tkinter.font import Font
from django.forms import DecimalField, model_to_dict
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection, transaction
from django.db.models import Sum, F
from django.urls import reverse
import datetime
from dateutil.relativedelta import relativedelta
from openpyxl import load_workbook
import openpyxl
import pandas as pd
import numpy as np
from reportlab.lib.styles import ParagraphStyle
from django.utils import timezone
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.db.models import Q
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from openpyxl.styles import Font, Alignment, PatternFill
from django.db.models import Q, Max
import datetime as dt_mod
from datetime import datetime, time

# Import the new Graph API service functions
from .services.outlook_graph_service import OutlookGraphService

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

# Import all models and forms
from .models import BillSettlement, CreditNote, DelegationNote, DelegationTransactionLog, EmailDelegation, ImportBank, JournalEntry, OutlookInbox, ReconnedBank, ScheduleSurplus, UnityBill, UnityClaimNote, UnityMgListing, ClientNotes, InternalFunds, UnityNotes, UnityClaim
from .forms import AddMemberForm, FiscalDateAssignmentForm, PreBillForm, UnityClaimForm

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from django.db.models import DateField, DateTimeField
from datetime import datetime, date

# --- Global Definitions ---
REVIEW_NOTES_OPTIONS = [
    "AWAIT 0101 REPORT",
    "AWAIT COVID APPROVAL",
    "BILLING FISCAL NOT AVAILABLE ON RFW",
    "DEBIT ADJUSTMENT",
    "GL0101 BALANCE NOT UTILISED",
    "HISTORIC CONTRIBUTIONS",
    "HISTORIC DEBIT - EMPLOYER TO PAY SHORTFALL",
    "NO SCHEDULE RECEIVED",
    "OVERS CREDIT LINE",
    "PARTIALLY RECONCILED",
    "RECONCILED",
    "REQUESTED SUPPORTING DOCUMENTS",
    "SALARY DOES NOT MATCH CONTRIBUTION RATE",
    "SCHEDULE DOES NOT MATCH PAYMENT",
]
ZERO_DECIMAL = Decimal('0.00')
# --------------------------

# --- Authentication Views ---
def login_view(request):
    """Handles user login."""
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
    """Displays the user dashboard with notification badges."""
    from .models import CreditNote, EmailDelegation, ReconnedBank
    
    username = request.user.username
    
    # Initialize counts
    pending_approval_count = 0
    new_emails_count = 0
    recycled_count = 0
    
    # 1. Manager Logic (Omega only)
    if username.lower() == 'omega' or request.user.is_superuser:
        # Financial Approvals (Managerial level)
        pending_approval_count = CreditNote.objects.filter(credit_link_status='Pending').count()
        
        # Inbox emails not yet assigned (Strictly NEW and work-related)
        new_emails_count = EmailDelegation.objects.filter(
            status='NEW', 
            assigned_user__isnull=True, 
            work_related=True
        ).count()
        
        # Recycle Bin: FIXED to match outlook_recycle_bin_view
        # Only count items explicitly marked with the 'DLT' status
        recycled_count = EmailDelegation.objects.filter(status='DLT').count()
    
    # 2. User Logic: My Assigned Tasks (Items explicitly marked as Delegated to current user)
    my_pending_delegations_count = EmailDelegation.objects.filter(
        assigned_user=request.user,
        status='DEL', # Standard status for delegated tasks in the agent's queue
        work_related=True
    ).count()

    # 3. Bank & Credit Note Logic
    # Count bank lines that require action (exclude Matched)
    bank_lines_count = ReconnedBank.objects.exclude(recon_status='Matched').count() 
    
    # Count pending credit notes for the badge indicator
    credit_notes_count = CreditNote.objects.filter(credit_link_status='Pending').count()
    
    context = {
        'username': username,
        'pending_approval_count': pending_approval_count,
        'new_emails_count': new_emails_count,
        'recycled_count': recycled_count,
        'my_pending_delegations_count': my_pending_delegations_count,
        'bank_lines_count': bank_lines_count,
        'credit_notes_count': credit_notes_count,
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

# --- Unity Listing Views ---
@login_required
def unity_list(request):
    """
    Displays a list combining InternalFunds and UnityMgListing.
    FIXED: Ensures newly added UnityMgListing records without InternalFunds 
    entries are correctly displayed.
    """
    
    # 1. Fetch Base Records
    internal_funds_records = InternalFunds.objects.all()
    
    # Create a mutable copy of the Unity listing map
    # We use a copy so we can pop items without affecting the database iteration
    unity_listing_map = {
        record.a_company_code: record for record in UnityMgListing.objects.all()
    }
    
    # --- NEW: Manual Calculation (Bypassing ORM Joins) ---
    
    # A. Create a Map: {Bill_ID : Company_Code}
    bill_map = dict(UnityBill.objects.values_list('id', 'C_Company_Code'))
    
    # B. Aggregate Total Surplus per Company
    surplus_map = defaultdict(Decimal)
    surpluses = ScheduleSurplus.objects.values('unity_bill_source_id', 'surplus_amount')
    
    for s in surpluses:
        b_id = s['unity_bill_source_id']
        amount = s['surplus_amount'] or ZERO_DECIMAL
        if b_id in bill_map:
            company_code = bill_map[b_id]
            surplus_map[company_code] += amount

    # C. Aggregate Total Allocation (Used Journal Entries) per Company
    allocation_map = defaultdict(Decimal)
    allocations = JournalEntry.objects.values('target_bill_id', 'amount')
    
    for a in allocations:
        b_id = a['target_bill_id']
        amount = a['amount'] or ZERO_DECIMAL
        if b_id in bill_map:
            company_code = bill_map[b_id]
            allocation_map[company_code] += amount

    # 3. Build Combined List - Phase 1: InternalFunds (primary source)
    combined_records = []
    
    for fund_record in internal_funds_records:
        company_code = fund_record.A_Company_Code
        
        # Pop the detail record if it exists, so we know it has been processed
        detail_record = unity_listing_map.pop(company_code, None)
        
        # --- Calculate Active Surplus ---
        total_gained = surplus_map.get(company_code, ZERO_DECIMAL)
        total_used = allocation_map.get(company_code, ZERO_DECIMAL)
        active_surplus_value = total_gained - total_used
        
        combined_data = {
            # Fields from InternalFunds
            'A_Company_Code': fund_record.A_Company_Code,
            'B_Company_Name': fund_record.B_Company_Name,
            'Source': fund_record.Source,
            'D_Company_Status': fund_record.D_Company_Status,
            
            # Fields from UnityMgListing (if matched)
            'c_agent': detail_record.c_agent if detail_record else None,
            'e_payment_method': detail_record.e_payment_method if detail_record else None,
            'f_billing_method': detail_record.f_billing_method if detail_record else None,
            'g_current_fiscal': detail_record.g_current_fiscal if detail_record else None,
            'h_current_status': detail_record.h_current_status if detail_record else None,
            'i_last_recon': detail_record.i_last_recon if detail_record else None,
            'j_arrears': detail_record.j_arrears if detail_record else None,
            'contact_email': detail_record.contact_email if detail_record else None,
            
            'has_details': bool(detail_record),
            'active_surplus': active_surplus_value,
        }
        combined_records.append(combined_data)

    # 3. Build Combined List - Phase 2: Remaining UnityMgListing records (System Only)
    for company_code, detail_record in unity_listing_map.items():
        
        # Calculate Active Surplus for this System-Only record
        total_gained = surplus_map.get(company_code, ZERO_DECIMAL)
        total_used = allocation_map.get(company_code, ZERO_DECIMAL)
        active_surplus_value = total_gained - total_used
        
        combined_data = {
            # Core fields from UnityMgListing
            'A_Company_Code': detail_record.a_company_code,
            'B_Company_Name': detail_record.b_company_name,
            'Source': 'System Only (New)', # Explicitly mark the source
            'D_Company_Status': detail_record.d_company_status,
            
            # Remaining fields from UnityMgListing
            'c_agent': detail_record.c_agent,
            'e_payment_method': detail_record.e_payment_method,
            'f_billing_method': detail_record.f_billing_method,
            'g_current_fiscal': detail_record.g_current_fiscal,
            'h_current_status': detail_record.h_current_status,
            'i_last_recon': detail_record.i_last_recon,
            'j_arrears': detail_record.j_arrears,
            'contact_email': detail_record.contact_email,
            
            'has_details': True, # It definitely has details, as it came from UnityMgListing
            'active_surplus': active_surplus_value,
        }
        combined_records.append(combined_data)
        
    # 4. Fetch Distinct Values for Filters
    distinct_source = InternalFunds.objects.values_list('Source', flat=True).distinct().exclude(Source__isnull=True).order_by('Source')
    # Since we are adding 'System Only (New)', we might need to update filters in the HTML/JS if we want to filter on it.
    
    distinct_company_status = InternalFunds.objects.values_list('D_Company_Status', flat=True).distinct().exclude(D_Company_Status__isnull=True).order_by('D_Company_Status')
    
    distinct_agent = UnityMgListing.objects.values_list('c_agent', flat=True).distinct().exclude(c_agent__isnull=True).order_by('c_agent')
    distinct_payment = UnityMgListing.objects.values_list('e_payment_method', flat=True).distinct().exclude(e_payment_method__isnull=True).order_by('e_payment_method')
    distinct_billing = UnityMgListing.objects.values_list('f_billing_method', flat=True).distinct().exclude(f_billing_method__isnull=True).order_by('f_billing_method')
    distinct_fiscal = UnityMgListing.objects.values_list('g_current_fiscal', flat=True).distinct().exclude(g_current_fiscal__isnull=True).order_by('g_current_fiscal')
    distinct_current_status = UnityMgListing.objects.values_list('h_current_status', flat=True).distinct().exclude(h_current_status__isnull=True).order_by('h_current_status')

    context = {
        'unity_records': combined_records,
        'distinct_source': distinct_source,
        'distinct_company_status': distinct_company_status,
        'distinct_agent': distinct_agent,
        'distinct_payment': distinct_payment,
        'distinct_billing': distinct_billing,
        'distinct_fiscal': distinct_fiscal,
        'distinct_current_status': distinct_current_status,
    }
    return render(request, 'unity_internal_app/unity_list.html', context)

from django.db.models import Sum, Max, Q # Ensure Max is imported

@login_required
def unity_information(request: HttpRequest, company_code):
    """
    Displays detailed information for a single record.
    UPDATED: Integrated Two-Pot claim sorting and refined Email Log badge logic.
    FIXED: Integrated OutlookInbox mapping for claim email previews.
    """
    
    # --- 1. Fetch Main Unity Record ---
    try:
        unity_record = UnityMgListing.objects.filter(a_company_code=company_code).first()
    except Exception:
        unity_record = None

    is_fallback = False
    lookup_code = company_code 
    
    if not unity_record:
        unity_record = InternalFunds.objects.filter(A_Company_Code=company_code).first()
        if not unity_record:
            messages.error(request, f"Error: Record {company_code} not found.")
            return redirect('unity_list')
        is_fallback = True
        messages.warning(request, f"Full detail information is not available for {company_code}.")

    # --- 2. Fetch Related Data ---
    notes = ClientNotes.objects.filter(a_company_code=company_code).order_by('-date')

    # --- Calculate Available Surplus ---
    company_bill_ids = UnityBill.objects.filter(C_Company_Code=lookup_code).values_list('id', flat=True)
    if company_bill_ids:
        total_created = ScheduleSurplus.objects.filter(
            unity_bill_source_id__in=company_bill_ids
        ).aggregate(total=Sum('surplus_amount'))['total'] or Decimal('0.00')

        surplus_ids = ScheduleSurplus.objects.filter(
            unity_bill_source_id__in=company_bill_ids
        ).values_list('id', flat=True)
        
        total_allocated = JournalEntry.objects.filter(
            surplus_source_id__in=surplus_ids
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        available_surplus_value = total_created - total_allocated
    else:
        available_surplus_value = Decimal('0.00')
    
    # --- Bankline Logic ---
    bank_lines_assigned = ReconnedBank.objects.filter(company_code=company_code).select_related('bank_line').order_by('-transaction_date')
    for line in bank_lines_assigned:
        total_settled_by_this_line = BillSettlement.objects.filter(
            reconned_bank_line_id=line.id
        ).aggregate(total=Sum('settled_amount'))['total'] or Decimal('0.00')
        line.true_remaining_balance = line.transaction_amount - total_settled_by_this_line
        line.is_fully_consumed = (line.true_remaining_balance <= Decimal('0.00'))
        line.original_assigned_amount = line.transaction_amount 
    
    bank_lines = bank_lines_assigned
    credit_notes = CreditNote.objects.filter(member_group_code=company_code).order_by('-ccdates_month')

    # --- UPDATED: Fetch Company Claims (Sorted for Two-Pot support) ---
    try:
        company_claims = UnityClaim.objects.filter(
            company_code=company_code
        ).prefetch_related('notes').order_by('-claim_created_date', 'member_surname')
        
        # FIXED: Logic to fetch email content using OutlookInbox mapping (Same as Two-Pot view)
        delegation_pks = [c.linked_email_id for c in company_claims if c.linked_email_id]
        
        if delegation_pks:
            # Map Delegation Primary Key -> Outlook String Email ID
            delegations_map = EmailDelegation.objects.in_bulk(delegation_pks)
            outlook_string_ids = [d.email_id for d in delegations_map.values()]
            
            # Map Outlook String Email ID -> Full Body/Subject Content
            inbox_map = OutlookInbox.objects.in_bulk(outlook_string_ids)

            for claim in company_claims:
                if claim.linked_email_id:
                    # Conversion to int to match in_bulk dictionary keys
                    del_obj = delegations_map.get(int(claim.linked_email_id))
                    if del_obj:
                        inbox_item = inbox_map.get(del_obj.email_id)
                        if inbox_item:
                            # Attach attributes for the template to render
                            claim.email_preview_subject = inbox_item.subject
                            claim.email_preview_sender = inbox_item.sender_address
                            claim.email_preview_body = inbox_item.body_content
                            claim.email_preview_date = inbox_item.received_at
    except Exception:
        company_claims = []
    
    # --- 3. Fetch Communication Logs (Notes/Calls) ---
    try:
        communication_logs = UnityNotes.objects.filter(member_group_code=lookup_code).filter(~Q(communication_type='Sent Email')).order_by('-date')
    except Exception:
        communication_logs = []
    
    # --- 4. Build Unified Email History ---
    combined_email_log = []
    
    delegated_emails = EmailDelegation.objects.filter(
        company_code=lookup_code
    ).select_related('assigned_user').order_by('-received_at')

    for task in delegated_emails:
        agg_result = DelegationTransactionLog.objects.filter(delegation=task).aggregate(latest=Max('timestamp'))
        latest_tx = agg_result.get('latest')

        combined_email_log.append({
            'type': 'Original', 
            'display_type': task.get_status_display(),
            'subject': task.email_category or f"Outlook Task: {task.email_id[:12]}...",
            'received_at': task.received_at,      
            'delegated_at': task.delegated_at,    
            'actioned_at': latest_tx,            
            'timestamp': task.received_at,        
            'action_user': f"System",
            'assigned_to': task.assigned_user.username if task.assigned_user else 'UNASSIGNED',
            'badge_color': '#3f51b5',
            'icon': '📥',
            'email_id': task.email_id,
            'log_id': f'delegation-{task.id}',
        })
        
        # Transactions associated with these tasks
        transactions = DelegationTransactionLog.objects.filter(delegation=task).select_related('user')
        for tx in transactions:
            is_reply = getattr(tx, 'email_type', 'DIRECT') == 'REPLY'
            
            combined_email_log.append({
                'type': 'Reply' if is_reply else 'Direct Sent',
                'display_type': tx.action_type, 
                'subject': tx.subject,
                'received_at': None,             
                'delegated_at': None,
                'actioned_at': tx.timestamp,      
                'timestamp': tx.timestamp,
                'action_user': tx.user.username if tx.user else 'System',
                'assigned_to': tx.recipient_email,
                'badge_color': '#9c27b0' if is_reply else '#f7931e', 
                'icon': '↩️' if is_reply else '📧',
                'email_id': task.email_id,        
                'log_id': f'transaction-{tx.id}',
            })
            
    # Direct Sent Emails from the UnityNotes table
    sent_emails_from_notes = UnityNotes.objects.filter(member_group_code=lookup_code, communication_type='Sent Email').order_by('-date')
    for log in sent_emails_from_notes:
        combined_email_log.append({
            'type': 'Direct Sent',
            'display_type': 'Direct Sent Email',
            'subject': log.action_notes or 'Email Sent',
            'received_at': None,
            'delegated_at': None,
            'actioned_at': log.date,
            'timestamp': log.date,
            'action_user': log.user,
            'badge_color': '#4CAF50',
            'icon': '📤',
            'log_id': f'notes-{log.ID}', 
        })

    combined_email_log.sort(key=lambda x: x['timestamp'], reverse=True)

    # --- 5. Billing Logic ---
    billing_queryset = UnityBill.objects.filter(C_Company_Code=lookup_code).order_by('-A_CCDatesMonth')
    open_bills, settled_bills = [], []
    for bill in list(billing_queryset):
        settled_sum = BillSettlement.objects.filter(unity_bill_source_id=bill.id).aggregate(total=Sum('settled_amount'))['total'] or Decimal('0.00')
        bill.total_covered = settled_sum
        if bill.is_reconciled:
            bill.display_status = 'RECON COMPLETE'
            bill.bankline_total = BillSettlement.objects.filter(unity_bill_source_id=bill.id, reconned_bank_line_id__isnull=False).aggregate(total=Sum('settled_amount'))['total'] or Decimal('0.00')
            bill.credit_allocated = BillSettlement.objects.filter(unity_bill_source_id=bill.id, source_credit_note_id__isnull=False).aggregate(total=Sum('settled_amount'))['total'] or Decimal('0.00')
            bill.surplus_allocated_from_journals = JournalEntry.objects.filter(target_bill_id=bill.id).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            bill.surplus_created = ScheduleSurplus.objects.filter(unity_bill_source_id=bill.id).aggregate(total=Sum('surplus_amount'))['total'] or Decimal('0.00')
            settled_bills.append(bill)
        else:
            bill.display_status = 'OPEN' if bill.total_covered > Decimal('0.00') else 'SCHEDULED'
            open_bills.append(bill)

    # --- Compose Select Logic ---
    my_delegated_emails = EmailDelegation.objects.filter(
        assigned_user=request.user
    ).exclude(
        status__in=['COMP', 'CLS', 'DONE'] 
    ).order_by('-received_at')

    # --- 6. HANDLE POST REQUESTS ---
    if request.method == 'POST':
        # HANDLE: Claims Modal "Send Email & Save" button
        if request.POST.get('email_submission_action') == 'send_email_and_log':
            subject = request.POST.get('member_email_subject_reply', 'Claim Update')
            recipient = request.POST.get('member_recipient_email')
            email_body_html = request.POST.get('email_body_html_content')
            
            if recipient and email_body_html:
                response = OutlookGraphService.send_outlook_email(settings.OUTLOOK_EMAIL_ADDRESS, recipient, subject, email_body_html, 'HTML')

                if response.get('success'):
                    UnityNotes.objects.create(
                        member_group_code=company_code,
                        user=request.user.username,
                        date=timezone.now(),
                        communication_type='Sent Email', 
                        action_notes=subject,
                        notes=f"To: {recipient}\n{email_body_html}"
                    )
                    messages.success(request, f"Email sent via Microsoft Graph to {recipient}!")
                else:
                    messages.error(request, f"Graph API Error: {response.get('error')}")

        if request.POST.get('update_general_info') == 'true':
            if unity_record and not is_fallback:
                unity_record.c_agent = request.POST.get('agent')
                unity_record.d_company_status = request.POST.get('company_status')
                unity_record.e_payment_method = request.POST.get('payment_method')
                unity_record.f_billing_method = request.POST.get('billing_method')
                unity_record.h_current_status = request.POST.get('current_status')
                unity_record.fund_status = request.POST.get('fund_status')
                unity_record.save()
                messages.success(request, "General Information updated.")
            return redirect('unity_information', company_code=company_code)
        
        else:
            action_type = request.POST.get('action') 
            if action_type == 'send_outgoing_member_note':
                subject = request.POST.get('member_email_subject_reply', 'Email Sent')
                recipient = request.POST.get('member_recipient_email', 'Unknown')
                email_body_html = request.POST.get('email_body_html_content')
                
                response = OutlookGraphService.send_outlook_email(settings.OUTLOOK_EMAIL_ADDRESS, recipient, subject, email_body_html, 'HTML')

                if response.get('success'):
                    UnityNotes.objects.create(
                        member_group_code=company_code,
                        user=request.user.username,
                        date=timezone.now(),
                        communication_type='Sent Email', 
                        action_notes=subject,
                        notes=f"To: {recipient}\n{email_body_html}"
                    )
                    messages.success(request, f"Email sent via Microsoft Graph to {recipient}!")
                else:
                    messages.error(request, f"Graph API Error: {response.get('error')}")
                
                return redirect(f"{reverse('unity_information', kwargs={'company_code': company_code})}#email-log")
            
            elif request.POST.get('note_content') or request.POST.get('action_notes'):
                UnityNotes.objects.create(
                    member_group_code=company_code,
                    user=request.user.username,
                    date=timezone.now(),
                    communication_type=request.POST.get('communication_type') or 'Notes Log',
                    action_notes=request.POST.get('action_notes'),
                    notes=request.POST.get('note_content')
                )
                messages.success(request, "Note added.")
                return redirect(f"{reverse('unity_information', kwargs={'company_code': company_code})}#notes-log")

    # --- 7. RENDER ---
    context = {
        'unity_record': unity_record,
        'notes': notes, 
        'communication_logs': communication_logs,
        'combined_email_log': combined_email_log, 
        'is_fallback': is_fallback,
        'bank_lines': bank_lines,
        'credit_notes': credit_notes,
        'open_bills': open_bills,
        'settled_bills': settled_bills,
        'company_claims': company_claims,
        'available_surplus': available_surplus_value, 
        'my_delegated_emails': my_delegated_emails,
    }
    return render(request, 'unity_internal_app/unity_information.html', context)

@login_required
def unity_billing_history(request, company_code):
    """
    Displays the billing history.
    UPDATED: Status logic now relies on G_Pre_Bill_Date and G_Schedule_Date.
    """
    # Requires: from django.db.models import Sum
    
    unity_record = UnityMgListing.objects.filter(a_company_code=company_code).first()
    is_fallback = False

    if not unity_record:
        unity_record = InternalFunds.objects.filter(A_Company_Code=company_code).first()
        is_fallback = True
    
    if not unity_record:
        messages.error(request, f"Company {company_code} not found.")
        return redirect('unity_list')

    # --- 2. FETCH BILLS ---
    billing_queryset = UnityBill.objects.filter(C_Company_Code=company_code).order_by('-A_CCDatesMonth')
    billing_records = list(billing_queryset)

    # --- 3. MANUAL CALCULATION LOOP & LIST SPLIT (UPDATED STATUS LOGIC) ---
    open_bills = []
    settled_bills = []
    
    for bill in billing_records:
        # A. Calculate Settlements
        settled_sum_agg = BillSettlement.objects.filter(
            unity_bill_source_id=bill.id
        ).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
        
        total_covered = settled_sum_agg
        scheduled_amount = bill.H_Schedule_Amount or ZERO_DECIMAL
        remaining_balance = scheduled_amount - total_covered
        
        # --- NEW & UPDATED STATUS LOGIC ---
        
        # Safely fetch date fields (using getattr for robustness)
        pre_bill_date = getattr(bill, 'F_Pre_Bill_Date', None)
        schedule_date = getattr(bill, 'G_Schedule_Date', None) # <--- USING G_Schedule_Date
        
        # 1. Final state check
        if bill.is_reconciled:
            display_status = 'RECON COMPLETE'
        
        # 2. Scheduled State: Schedule Date (G_Schedule_Date) AND Amount (H_Schedule_Amount) completed.
        elif schedule_date and scheduled_amount > ZERO_DECIMAL:
            # If it's scheduled and not reconciled, check if reconciliation has started.
            if total_covered > ZERO_DECIMAL:
                display_status = 'OPEN' # Scheduled and currently being reconciled
            else:
                display_status = 'SCHEDULED' # Scheduled but no settlements yet (new status)
                
        # 3. Pre-Bill State: Pre-Bill Date (G_Pre_Bill_Date) is set, but no Schedule Date.
        elif pre_bill_date and not schedule_date:
            display_status = 'PRE-BILL' # New status, awaiting scheduling details

        # 4. Fallback
        else:
            if scheduled_amount > ZERO_DECIMAL and total_covered > ZERO_DECIMAL:
                display_status = 'OPEN'
            elif scheduled_amount > ZERO_DECIMAL:
                display_status = 'OPEN'
            else:
                display_status = 'Pre-Bill' # General state for records with no defined stage
                
        # --- END NEW & UPDATED STATUS LOGIC ---

        bill.temp_remaining = remaining_balance
        bill.total_covered = total_covered
        bill.display_status = display_status

        if bill.display_status == 'RECON COMPLETE':
            settled_bills.append(bill)
        else:
            open_bills.append(bill)

    # --- 4. FETCH DATA FOR THE 'BANK LINES & CREDIT' TAB ---
    # Note: The bank lines here should use the same enhanced logic as unity_information if showing remaining balance
    bank_lines_assigned = ReconnedBank.objects.filter(company_code=company_code).select_related('bank_line').order_by('-transaction_date')
    for line in bank_lines_assigned:
        total_settled_by_this_line = BillSettlement.objects.filter(
            reconned_bank_line_id=line.id
        ).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
        line.true_remaining_balance = line.transaction_amount - total_settled_by_this_line
        line.is_fully_consumed = (line.true_remaining_balance <= ZERO_DECIMAL)
    bank_lines_data = bank_lines_assigned
    
    credit_notes_data = CreditNote.objects.filter(member_group_code=company_code).order_by('-ccdates_month')

    context = {
        'company_code': company_code,
        'unity_record': unity_record,
        'is_fallback': is_fallback,
        'bank_lines': bank_lines_data,
        'credit_notes': credit_notes_data,
        'open_bills': open_bills,
        'settled_bills': settled_bills,
        'billing_records': billing_records,
        'default_tab_override': '#recon',
    }
    
    return render(request, 'unity_internal_app/unity_information.html', context)

# --- PRE-BILL CREATION VIEW ---
@login_required
@transaction.atomic
def create_pre_bill(request, company_code):
    """
    Handles the creation of a new UnityBill record, setting the Pre-Bill Date.
    """
    # Requires: from django.db.models import Sum, F
    
    company_name = f"Company Code {company_code}"
    
    # 1. Fetch Company Info
    try:
        company_info = InternalFunds.objects.get(A_Company_Code=company_code)
        company_name = company_info.B_Company_Name
    except InternalFunds.DoesNotExist:
        messages.error(request, f"Cannot find company details for code {company_code}.")
        return redirect('unity_information', company_code=company_code)

    calculated_debt_for_prefill = ZERO_DECIMAL
    
    # 2. Handle Form Submission (POST)
    if request.method == 'POST':
        form = PreBillForm(request.POST)
        bill_date_str = request.POST.get('A_CCDatesMonth')
        bill_date = None
        
        if bill_date_str:
            try:
                bill_date = datetime.strptime(bill_date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, "Invalid date format submitted.")

        if form.is_valid() and bill_date:
            
            # --- NEW LOGIC: Calculate Debt (All available) ---
            # NOTE: We fetch ALL available debt, regardless of fiscal date, for pre-fill purposes.
            # This calculation is for guidance only, as it's not restricted by fiscal month anymore.
            debt_queryset = ReconnedBank.objects.filter(
                company_code=company_code,
                # Only unsettled lines
                amount_settled__lt=F('transaction_amount'),
            ).annotate(
                remaining_debt=F('transaction_amount') - F('amount_settled')
            )
            calculated_debt_for_prefill = debt_queryset.aggregate(
                total_schedule_amount=Sum('remaining_debt')
            )['total_schedule_amount'] or ZERO_DECIMAL
            # --- END NEW LOGIC ---
            
            bill_record = form.save(commit=False)
            bill_record.C_Company_Code = company_code
            
            # --- NEW LOGIC: Set Pre-Bill Date upon creation ---
            # This triggers the 'PRE-BILL' status as G_Schedule_Date will be None
            bill_record.F_Pre_Bill_Date = timezone.now().date()
            
            # Check the actual schedule amount being saved by the user
            scheduled_amount = bill_record.H_Schedule_Amount or ZERO_DECIMAL
            
            # --- CRITICAL FIX: Prevent premature closure ---
            if scheduled_amount <= ZERO_DECIMAL:
                # If R0.00 is scheduled, force the bill to remain OPEN/PRE-BILL by clearing final dates.
                bill_record.J_Final_Date = None
                # I_Submitted_Date is cleared here, which is fine since G_Schedule_Date controls the status now.
                bill_record.I_Submitted_Date = None
                messages.warning(request, "Bill created with R0.00 scheduled amount. It will remain in Pre-Bill status until updated.")
            # --- END CRITICAL FIX ---
            
            try:
                bill_record.save()
                
                messages.success(request, f"New Pre-Bill record created for {company_code} (Date: {bill_record.A_CCDatesMonth}). Scheduled Amount: R{bill_record.H_Schedule_Amount}")
                
                # 🛑 CRITICAL FIX: Add cache-busting timestamp to the redirect URL
                timestamp = timezone.now().timestamp()
                return redirect(f"{reverse('unity_billing_history', kwargs={'company_code': company_code})}?cache={timestamp}")
                
            except Exception as e:
                messages.error(request, f"Error saving new bill: {e}")
                
        else:
            messages.error(request, "Please correct the errors in the form and ensure the Bill Date is valid.")
    
    # 3. Handle GET Request (Initial Form Display)
    else:
        # 4. Final Context Construction for GET
        initial_data = {
            'C_Company_Code': company_code,
            'D_Company_Name': company_name,
            # Pre-fill with the calculated debt
            'H_Schedule_Amount': calculated_debt_for_prefill
        }
        form = PreBillForm(initial=initial_data)

    context = {
        'form': form,
        'company_code': company_code,
        'company_name': company_name,
        'is_editing': False,
    }
    return render(request, 'unity_internal_app/bill_form.html', context)

@login_required
def add_member_view(request):
    """Handles adding a new UnityMgListing member."""
    # NOTE: AddMemberForm must be imported or mocked above for runtime testing
    if request.method == 'POST':
        form = AddMemberForm(request.POST)
        if form.is_valid():
            try:
                # This form saves to the UnityMgListing table (internal_mg_list)
                form.save()
                messages.success(request, f"New member '{form.cleaned_data['b_company_name']}' added successfully!")
                return redirect('unity_list')
            except Exception as e:
                messages.error(request, f"Error saving member: {e}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AddMemberForm()

    context = {
        'form': form,
    }
    return render(request, 'unity_internal_app/add_member.html', context)

# --- Bank Reconciliation Views ---
@login_required
def import_excel_view(request):
    """Handles the upload and import of Excel data."""
    from django.db import connection
    from .models import ImportBank
    import pandas as pd
    import numpy as np
    
    if request.method == 'POST':
        if 'excel_file' in request.FILES:
            excel_file = request.FILES['excel_file']
            
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                messages.error(request, "Invalid file format. Please upload an Excel (.xlsx or .xls) file.")
                return redirect('import_data')
            
            try:
                df = pd.read_excel(excel_file, keep_default_na=False, header=None)
                
                db_columns = [
                    'Bank_account_name', 'Account_number', 'Statement_reference',
                    'DATE', 'Balance', 'Transaction_amount', 'Transaction_description',
                    'INTERNAL_IDENTIFICATION', 'Specialist', 'Date_identified',
                    'Fiscal', 'Comments', 'Interim_fiscal'
                ]
                df.columns = db_columns
                
                df = df.astype(str).replace({'nan': '', 'NaT': ''})
                
                df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
                df['Date_identified'] = pd.to_datetime(df['Date_identified'], errors='coerce').dt.date
                df['Balance'] = pd.to_numeric(df['Balance'], errors='coerce')
                df['Transaction_amount'] = pd.to_numeric(df['Transaction_amount'], errors='coerce')
                
                initial_count = len(df)
                df.dropna(subset=['DATE'], inplace=True)
                dropped_count = initial_count - len(df)
                
                if dropped_count > 0:
                    messages.warning(request, f"Skipped {dropped_count} row(s) due to missing or invalid required data (Date).")

                df['DATE'] = df['DATE'].dt.date
                df = df.replace(r'^\s*$', np.nan, regex=True)
                df = df.where(pd.notna(df), None)

                with transaction.atomic():
                    columns_sql = ', '.join([f'`{col}`' for col in db_columns])
                    placeholders = ', '.join(['%s'] * len(db_columns))
                    sql = f"INSERT INTO {ImportBank._meta.db_table} ({columns_sql}) VALUES ({placeholders})"
                    
                    data_to_insert = []
                    for row in df[db_columns].values:
                        cleaned_row = [None if isinstance(item, float) and np.isnan(item) else item for item in row]
                        data_to_insert.append(tuple(cleaned_row))

                    with connection.cursor() as cursor:
                        cursor.executemany(sql, data_to_insert)
                        
                messages.success(request, f"Successfully imported {len(df)} records into the 'importbank' table. Data was appended.")
                
            except Exception as e:
                messages.error(request, f"An error occurred during import: {e}")
            
            return redirect('import_data')

    return render(request, 'unity_internal_app/import_excel.html', {})

@login_required
def bank_list(request):
    """
    Displays a list of active bank transaction segments, combining both existing
    ReconnedBank segments (splits, partials) and brand new, unassigned ImportBank lines.
    
    CRITICAL FIX: All active lines are now sourced from the ReconnedBank table.
    New ImportBank lines are automatically converted to ReconnedBank segments on load.
    """
    from django.db.models import F, Q

    # --- Step 1: Automatic Segment Creation for New Imports ---
    
    # Identify ImportBank IDs that are NOT in the ReconnedBank table at all
    assigned_import_ids = ReconnedBank.objects.values_list('bank_line_id', flat=True).distinct()
    
    new_imports_to_segment = ImportBank.objects.exclude(
        id__in=assigned_import_ids
    ).filter(
        # Only process positive transactions
        transaction_amount__gt=ZERO_DECIMAL 
    )
    
    # Use transaction.atomic to ensure segment creation is robust
    with transaction.atomic():
        for import_line in new_imports_to_segment:
            # Create the initial 1:1 segment in ReconnedBank, marked as unassigned
            ReconnedBank.objects.create(
                bank_line_id=import_line.id,
                company_code=None,  # Crucially starts as UNASSIGNED
                transaction_amount=import_line.transaction_amount,
                transaction_date=import_line.date,
                fiscal_date=None, 
                recon_status='Unidentified - New Import', # Specific status for first segment
                amount_settled=ZERO_DECIMAL,
            )
            
    # --- Step 2: Query ALL Active Segments (New Imports + Split Pushbacks) ---
    
    # Query all ReconnedBank segments that have a remaining balance
    active_segments_queryset = ReconnedBank.objects.annotate(
        remaining_balance=F('transaction_amount') - F('amount_settled')
    ).filter(
        remaining_balance__gt=ZERO_DECIMAL 
    ).select_related('bank_line').order_by('-transaction_date', 'id')

    # --- Step 3: Combine and Process ---
    
    combined_records = []
    
    for recon_data in active_segments_queryset:
        
        allocated_code = recon_data.company_code
        # A line is considered 'unassigned' if company_code is NULL/None
        is_unassigned = allocated_code is None 
        
        # --- Company & Agent Info ---
        company_name = "-"
        agent_name = "-"
        if allocated_code and allocated_code != "N/A":
            mg_entry = UnityMgListing.objects.filter(a_company_code=allocated_code).first()
            if mg_entry:
                company_name = mg_entry.b_company_name
                agent_name = mg_entry.c_agent
            else:
                fund_entry = InternalFunds.objects.filter(A_Company_Code=allocated_code).first()
                if fund_entry:
                    company_name = fund_entry.B_Company_Name
                    agent_name = "Internal"
        
        # --- Action Logic (Uses ReconnedBank PK only) ---
        # If unassigned, the action is 'Assign' and the target ID is the ReconnedBank ID.
        # If assigned, the action is 'View' and the target ID is the ReconnedBank ID.
        action_url = reverse('bankline_recon', args=[recon_data.id]) if is_unassigned else reverse('display_bankline_review', args=[recon_data.id])
        action_text = "Assign" if is_unassigned else "View"
        display_status = recon_data.recon_status or "Unidentified" # Use actual status for segments
        
        combined_records.append({
            # Data from ReconnedBank segment (Primary Key is ALWAYS ReconnedBank ID)
            'id': recon_data.id, 
            'deposit_amount': recon_data.transaction_amount, 
            'transaction_date': recon_data.transaction_date,
            'transaction_description': recon_data.bank_line.transaction_description,
            'remaining_balance': recon_data.remaining_balance,
            'recon_status': display_status,
            'allocated_code': allocated_code,
            'company_name': company_name,
            'agent': agent_name,
            'review_note': recon_data.review_note, 
            'action_url': action_url,
            'action_text': action_text,
        })

    # Sort the final combined list by date
    combined_records.sort(key=lambda x: x['transaction_date'], reverse=True)
    
    context = {
        'bank_records': combined_records,
    }
    return render(request, 'unity_internal_app/bank_list.html', context)

@login_required
def bankline_recon(request, record_id):
    """
    Handles the initial reconciliation (assignment) of a single bank line segment.
    CRITICAL FIX: Now expects a ReconnedBank ID (record_id) and directly updates it.
    """
    # 1. Fetch the ReconnedBank segment (new import segment or split remainder)
    try:
        recon_segment = get_object_or_404(
            ReconnedBank.objects.select_related('bank_line'), 
            id=record_id
        )
    except Exception:
        messages.error(request, f"Error retrieving Recon Segment ID: {record_id}")
        return redirect('bank_list')

    # Check if segment is already assigned (in which case, redirect to review)
    if recon_segment.company_code is not None:
        messages.warning(request, f"Bank line {record_id} is already assigned to {recon_segment.company_code}. Redirecting to review.")
        return redirect('display_bankline_review', recon_id=record_id)
        
    # Get all potential Company Codes from the InternalFunds source table
    # This is the list displayed in the dropdown
    company_codes = InternalFunds.objects.values_list('A_Company_Code', flat=True).distinct().order_by('A_Company_Code')

    if request.method == 'POST':
        allocated_company_code_value = request.POST.get('company_code')
        
        if not allocated_company_code_value or allocated_company_code_value == 'None':
            messages.error(request, "You must select a Company Code for reconciliation.")
            return redirect('bankline_recon', record_id=record_id)

        try:
            # --- VALIDATION STEP: Ensure the code exists in a lookup table ---
            # Check if the code exists in either InternalFunds or UnityMgListing
            code_exists = InternalFunds.objects.filter(A_Company_Code=allocated_company_code_value).exists() or \
                          UnityMgListing.objects.filter(a_company_code=allocated_company_code_value).exists()

            if not code_exists:
                messages.error(request, f"Company code '{allocated_company_code_value}' is not recognized as a valid Member Group.")
                return redirect('bankline_recon', record_id=record_id)

            # --- ASSIGNMENT ---
            recon_segment.company_code = allocated_company_code_value
            recon_segment.agent = request.user.get_full_name() or request.user.username
            
            # Set status to 'Unreconciled - Assigned'
            recon_segment.recon_status = 'Unreconciled - Assigned'
            
            recon_segment.save()
            
            messages.success(request, f"Bank line segment {record_id} assigned to Code: {allocated_company_code_value}.")
            
            # Redirect to the Member Group's info page, forcing the reconciliation tab
            return redirect(f"{reverse('unity_information', kwargs={'company_code': allocated_company_code_value})}#recon")

        except Exception as e:
            messages.error(request, f"Error saving assignment: {e}")
            return redirect('bankline_recon', record_id=record_id)

    # GET Request context
    context = {
        # 'bank_record' is the parent ImportBank object (original transaction details)
        'bank_record': recon_segment.bank_line, 
        'company_codes': company_codes,
        'current_recon': recon_segment, # Pass the segment object for its details
    }
    return render(request, 'unity_internal_app/bankline_recon.html', context)

@login_required
def generate_recon_statement(request, recon_id):
    """Generates a PDF statement for a single reconciled bank line."""
    try:
        recon_record = get_object_or_404(ReconnedBank, pk=recon_id)
        company_listing = get_object_or_404(
            InternalFunds,
            A_Company_Code=recon_record.company_code
        )
    except Exception as e:
        messages.error(request, f"Error fetching PDF data: {e}")
        return redirect('bank_list')
    
    response = HttpResponse(content_type='application/pdf')
    filename = f"Recon_Statement_{recon_record.company_code}_{recon_id}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'

    try:
        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter
        styles = getSampleStyleSheet()

        x_margin = inch
        y_cursor = height - inch

        p.setFont("Helvetica-Bold", 16)
        p.drawString(x_margin, y_cursor, "Unity Management Reconciliation Statement")
        y_cursor -= 0.3 * inch

        p.setFont("Helvetica-Bold", 10)
        p.drawString(x_margin, y_cursor, "Company Details:")
        y_cursor -= 0.2 * inch

        data_rows = [
            ("Company Name:", company_listing.B_Company_Name),
            ("Company Code:", recon_record.company_code),
            ("Statement Date:", timezone.now().strftime("%B %d, %Y")),
        ]

        p.setFont("Helvetica", 10)
        for label, value in data_rows:
            p.drawString(x_margin, y_cursor, label)
            p.drawString(x_margin + 2.5 * inch, y_cursor, str(value))
            y_cursor -= 0.2 * inch
        
        y_cursor -= 0.3 * inch

        p.setFont("Helvetica-Bold", 10)
        p.drawString(x_margin, y_cursor, "Transaction Details:")
        y_cursor -= 0.2 * inch
        
        transaction_data = [
            ("Reconciliation ID:", recon_id),
            ("Date Received:", recon_record.transaction_date.strftime("%Y-%m-%d")),
            ("Amount:", f"R{recon_record.transaction_amount}"),
            ("Status:", recon_record.recon_status),
            ("Fiscal Review:", recon_record.fiscal_date.strftime("%Y-%m-%d") if recon_record.fiscal_date else "N/A"),
            ("Note:", recon_record.review_note if recon_record.review_note else "None"),
        ]
        
        p.setFont("Helvetica", 10)
        for label, value in transaction_data:
            p.drawString(x_margin, y_cursor, label)
            p.drawString(x_margin + 2.5 * inch, y_cursor, str(value))
            y_cursor -= 0.2 * inch

        p.setFont("Helvetica-Bold", 10)
        p.drawString(x_margin, y_cursor, "Source Description:")
        y_cursor -= 0.2 * inch
        
        p.setFont("Helvetica", 10)
        description_text = str(recon_record.bank_line.transaction_description)
        if 'Normal' not in styles:
            styles.add(ParagraphStyle(name='Normal'))
        
        description_paragraph = Paragraph(description_text, styles['Normal'])
        
        description_paragraph.wrapOn(p, width - 2 * x_margin, height)
        
        description_paragraph.drawOn(p, x_margin, y_cursor - description_paragraph.height)
        y_cursor -= description_paragraph.height + 0.1 * inch

        p.showPage()
        p.save()
        return response

    except Exception as e:
        messages.error(request, f"PDF Drawing/ReportLab Failure: {e}")
        return redirect('bank_list')
    
# --- BANKLINE REVIEW VIEWS ---
@login_required
def display_bankline_review(request, recon_id):
    """Displays a single reconciled bank line for review, unpacking the note field."""
    is_from_unity_info = request.GET.get('source') == 'unity'
    recon_record = get_object_or_404(ReconnedBank.objects.select_related('bank_line'), pk=recon_id)
    
    # --- UNPACK THE NOTE FIELD ---
    unpacked_category = ""
    unpacked_custom_text = ""

    if recon_record.review_note:
        if " | " in recon_record.review_note:
            # Splits into exactly 2 parts at the first pipe found
            parts = recon_record.review_note.split(" | ", 1)
            unpacked_category = parts[0]
            unpacked_custom_text = parts[1]
        else:
            # If no pipe, assume the whole thing is the category
            unpacked_category = recon_record.review_note

    company_codes = InternalFunds.objects.values_list('A_Company_Code', flat=True).distinct().order_by('A_Company_Code')

    context = {
        'recon_record': recon_record,
        'bank_record': recon_record.bank_line,
        'company_codes': company_codes,
        'review_notes': REVIEW_NOTES_OPTIONS,
        'current_category': unpacked_category,        # Separate variable for dropdown
        'current_custom_text': unpacked_custom_text,  # Separate variable for textarea
        'is_from_unity_info': is_from_unity_info,
    }
    return render(request, 'unity_internal_app/display_bankline_review.html', context)

@login_required
@transaction.atomic
def update_bankline_details(request, recon_id):
    """Updates ReconnedBank by packing Category and Text into the single review_note field."""
    recon_record = get_object_or_404(ReconnedBank, pk=recon_id)
    
    if request.method == 'POST':
        new_company_code = request.POST.get('company_code_select')
        new_fiscal_date = request.POST.get('fiscal_date')
        
        # 1. Capture fields separately from the form
        category = request.POST.get('review_note', '').strip()
        custom_text = request.POST.get('review_note_text', '').strip()

        # 2. Pack them into the single available field using a separator
        # Format saved to DB: "Category Name | Custom detailed note text"
        if category and custom_text:
            combined_note = f"{category} | {custom_text}"
        else:
            combined_note = category or custom_text

        # 3. Update fields
        allocation_cleared = (new_company_code in [None, '', 'None'])
        recon_record.company_code = new_company_code if new_company_code else None
        recon_record.fiscal_date = new_fiscal_date if new_fiscal_date else None
        recon_record.review_note = combined_note # Store the packed string
        
        old_status = recon_record.recon_status
        new_status = old_status

        # --- STATUS LOGIC ---
        if allocation_cleared:
            new_status = None
        elif recon_record.company_code:
            new_status = 'Unreconciled - Allocated' if recon_record.fiscal_date else 'Unreconciled - Assigned'
        
        # Check the 'category' part specifically for status override
        if category and "Query required" in category:
            new_status = 'Review Pending'
        
        if new_status != old_status:
            messages.info(request, f"Status updated to '{new_status or 'Unidentified'}'.")

        recon_record.recon_status = new_status if new_status is not None else ''
        recon_record.save()

        # 4. Sync to original bank line comments
        bank_line = recon_record.bank_line
        bank_line.comments = f"Reviewed: {combined_note} (Code: {recon_record.company_code or 'N/A'})"
        bank_line.save()
        
        messages.success(request, f"Bank Line {recon_id} details saved.")
        return redirect('display_bankline_review', recon_id=recon_id)
    
    return redirect('display_bankline_review', recon_id=recon_id)

# --- BILLING HELPER FUNCTION (NOW OBSOLETE/OVERWRITTEN) ---
# KEPT FOR CONTEXT, BUT WILL BE OVERWRITTEN BY NEW LOGIC
# def calculate_bill_debt(...)

# --- NEW HELPER FUNCTION FOR FLEXIBLE ALLOCATION (Replaces old calculate_bill_debt logic) ---
def get_available_bank_lines(company_code):
    """
    Returns a queryset of ReconnedBank lines that have remaining unsettled amounts 
    for the specific company code, regardless of fiscal date.
    """
    return ReconnedBank.objects.filter(
        company_code=company_code,
        # Check if the line has money remaining
        amount_settled__lt=F('transaction_amount'),
    ).select_related('bank_line').annotate(
        remaining_debt=F('transaction_amount') - F('amount_settled')
    ).order_by('transaction_date')

# --- BILLING RECONCILIATION VIEWS (UPDATED FOR FLEXIBLE ALLOCATION) ---
from decimal import Decimal
# NOTE: Ensure necessary imports like Decimal, Sum, timezone, etc. are at the top of your views.py

@login_required
def pre_bill_reconciliation_summary(request, company_code, bill_id):
    # Define a small tolerance for Decimal comparisons
    SAFETY_TOLERANCE = Decimal('0.0001') 
    ZERO_DECIMAL = Decimal('0.00')
    
    bill_record = get_object_or_404(UnityBill, id=bill_id, C_Company_Code=company_code)
    
    # --- CALCULATE AVAILABLE DEBT ---
    available_debt_lines = get_available_bank_lines(company_code)
    total_debt = available_debt_lines.aggregate(total=Sum('remaining_debt'))['total'] or ZERO_DECIMAL
    
    bill_date = bill_record.A_CCDatesMonth
    month_start_date = bill_date.replace(day=1)
    next_month = month_start_date + relativedelta(months=1)
    fiscal_end_date = next_month - relativedelta(days=1)

    # --- AGGREGATIONS ---
    
    # 1. TOTAL APPLIED TO BILL: Total settled amount from all sources
    total_applied = BillSettlement.objects.filter(
        unity_bill_source_id=bill_record.pk
    ).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
    
    # 2. SEPARATE CASH ALREADY APPLIED
    total_cash_applied = BillSettlement.objects.filter(
        unity_bill_source_id=bill_record.pk,
        reconned_bank_line_id__isnull=False 
    ).aggregate(total_cash=Sum('settled_amount'))['total_cash'] or ZERO_DECIMAL

    # 3. Get Credit Total
    total_credit_notes_assigned = BillSettlement.objects.filter(
        unity_bill_source_id=bill_record.pk,
        source_credit_note_id__isnull=False
    ).aggregate(total_credit=Sum('settled_amount'))['total_credit'] or ZERO_DECIMAL

    # 4. Get Journal/Surplus Total (from JournalEntry table)
    total_surplus_applied_to_bill = JournalEntry.objects.filter(
        target_bill=bill_record
    ).aggregate(total_footer=Sum('amount'))['total_footer'] or ZERO_DECIMAL

    # --- MATH UPDATES ---
    scheduled_amount = bill_record.H_Schedule_Amount or ZERO_DECIMAL
    
    # Remaining Schedule logic
    remaining_scheduled_amount = scheduled_amount - total_credit_notes_assigned - total_surplus_applied_to_bill - total_cash_applied
    
    # Outstanding card
    current_outstanding = max(ZERO_DECIMAL, remaining_scheduled_amount)

    # Surplus Logic
    over_scheduled_amount = max(ZERO_DECIMAL, total_debt - current_outstanding)

    # --- FIND AVAILABLE SURPLUS FOR THIS COMPANY ---
    company_bill_ids = UnityBill.objects.filter(C_Company_Code=company_code).values_list('id', flat=True)
    potential_surpluses = ScheduleSurplus.objects.filter(
        unity_bill_source_id__in=company_bill_ids
    ).exclude(status='FULLY_APPLIED')
    
    available_surpluses = []
    total_available_surplus_value = ZERO_DECIMAL
    
    for s in potential_surpluses:
        used = JournalEntry.objects.filter(surplus_source=s).aggregate(t=Sum('amount'))['t'] or ZERO_DECIMAL
        remaining = s.surplus_amount - used
        if remaining > ZERO_DECIMAL:
            s.temp_available = remaining
            total_available_surplus_value += remaining
            try:
                origin_bill = UnityBill.objects.get(pk=s.unity_bill_source_id)
                s.origin_date = origin_bill.A_CCDatesMonth
            except:
                s.origin_date = "Unknown Date"
            available_surpluses.append(s)

    # --- FETCH APPLIED JOURNALS FOR DISPLAY ---
    applied_journals = JournalEntry.objects.filter(target_bill=bill_record).select_related('surplus_source')

    # --- NEW: FETCH ASSIGNED CREDIT NOTES FOR DISPLAY ---
    # We query the Settlements table to find any credit notes that have been 
    # used (even partially) for this bill.
    assigned_note_ids = BillSettlement.objects.filter(
        unity_bill_source_id=bill_record.pk,
        source_credit_note_id__isnull=False
    ).values_list('source_credit_note_id', flat=True)
    
    # Get the actual CreditNote objects based on those IDs
    credit_notes_queryset = CreditNote.objects.filter(id__in=assigned_note_ids)
    
    # --- UPDATED ACTION MESSAGE LOGIC ---
    is_bill_fully_covered = total_applied >= (scheduled_amount - SAFETY_TOLERANCE)
    
    if is_bill_fully_covered:
        is_proceed_enabled = True
        settled_vs_scheduled_diff = total_applied - scheduled_amount
        if settled_vs_scheduled_diff >= SAFETY_TOLERANCE:
             action_message = f"FULLY COVERED. R{settled_vs_scheduled_diff:.2f} recorded as surplus. Ready to Finalize."
        else:
             action_message = "PERFECTLY COVERED. Ready to Finalize."
    elif total_debt > ZERO_DECIMAL: 
        if total_debt >= remaining_scheduled_amount:
             action_message = f"FULL CASH COVERAGE AVAILABLE: R{total_debt:.2f} can clear the R{remaining_scheduled_amount:.2f} balance."
             is_proceed_enabled = True 
        else:
             action_message = f"Partial coverage available. R{total_debt:.2f} can be applied to the R{remaining_scheduled_amount:.2f} balance."
             is_proceed_enabled = False
    else: 
        is_proceed_enabled = False
        action_message = f"Action REQUIRED: R{remaining_scheduled_amount:.2f} liability remains."

    # --- FINAL CONTEXT MAPPING ---
    context = {
        'bill_record': bill_record,
        'company_code': company_code,
        'total_debt': total_debt,
        'scheduled_amount': scheduled_amount,
        'total_credit_notes_assigned': total_credit_notes_assigned,
        'total_available_surplus': total_available_surplus_value,
        'total_cash_applied': total_cash_applied,
        'remaining_schedule_amount': remaining_scheduled_amount,
        'current_outstanding': current_outstanding, 
        'over_scheduled_amount': over_scheduled_amount,
        'all_lines': available_debt_lines.all().order_by('transaction_date'),
        
        # USE THE NEW QUERYSET HERE:
        'credit_notes': credit_notes_queryset,
        
        'available_surpluses': available_surpluses,
        'applied_journals': applied_journals,
        'total_journal_assigned': total_surplus_applied_to_bill,
        'action_message': action_message,
        'is_proceed_enabled': is_proceed_enabled,
        'fiscal_starting_date': month_start_date,
        'fiscal_closing_date': fiscal_end_date,
    }
    
    return render(request, 'unity_internal_app/pre_bill_summary.html', context)

@login_required
@transaction.atomic
def process_bill_settlement(request, company_code, bill_id):
    """***FUNCTION DISABLED***"""
    messages.error(request, "Settlement processing is disabled due to the exclusion of Deposit Amount logic.")
    return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)

def get_bank_lines_used_in_settlement(bill_record):
    """
    Retrieves the unique ReconnedBank lines that were applied to the given UnityBill 
    for the final summary table.
    """
    # 1. Get the primary keys (IDs) of all ReconnedBank lines found in the BillSettlement audit trail for this bill.
    used_line_ids = BillSettlement.objects.filter(
        unity_bill_source_id=bill_record.id
    ).values_list('reconned_bank_line_id', flat=True).distinct()
    
    # 2. Retrieve the ReconnedBank objects corresponding to those IDs.
    # Assumes ReconnedBank has a ForeignKey 'bank_line' for descriptions.
    used_lines = ReconnedBank.objects.filter(
        id__in=used_line_ids
    ).select_related('bank_line').order_by('transaction_date')
    
    return used_lines

# Note: The other two helpers (calculate_total_settled_for_display and 
# calculate_total_credit_assigned) are now calculated directly inside 
# reconciliation_success_view, making explicit helper functions unnecessary.

# --- CORE VIEW FUNCTIONS ---

# --- HELPER FUNCTIONS DEFINITIONS (To resolve Pylance errors and ensure data integrity) ---

def get_bank_lines_used_in_settlement(bill_record):
    """
    Retrieves the unique ReconnedBank lines that were applied to the given UnityBill 
    for the final summary table.
    """
    # 1. Get the primary keys (IDs) of all ReconnedBank lines found in the BillSettlement audit trail for this bill.
    used_line_ids = BillSettlement.objects.filter(
        unity_bill_source_id=bill_record.id
    ).values_list('reconned_bank_line_id', flat=True).distinct()
    
    # 2. Retrieve the ReconnedBank objects corresponding to those IDs.
    # We use select_related to efficiently fetch the description from the related BankLine table.
    used_lines = ReconnedBank.objects.filter(
        id__in=used_line_ids
    ).select_related('bank_line').order_by('transaction_date')
    
    return used_lines

# --- CORE VIEW FUNCTIONS ---

@login_required
@transaction.atomic
def process_cash_allocation(request, company_code, bill_id):
    """
    Handles cash allocation for a single selected bank line.
    REVISED: Ensures remainders are fully moved to CreditNote and the bank line is closed.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)

    aware_dt = timezone.now()
    selected_recon_id = request.POST.get('selected_recon_id')
    amount_to_apply_str = request.POST.get('amount_to_apply')
    should_split_and_reallocate = request.POST.get('split_and_reallocate') == 'True' 

    if not selected_recon_id:
        messages.error(request, "Allocation failed: No Bank Line selected.")
        return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)
        
    try:
        amount_to_apply = Decimal(amount_to_apply_str) 
        if amount_to_apply <= ZERO_DECIMAL:
            messages.error(request, "Allocation failed: Amount must be greater than zero.")
            return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)
            
        # 1. Lock records
        recon_line = ReconnedBank.objects.select_for_update().get(pk=selected_recon_id, company_code=company_code)
        bill_record = UnityBill.objects.select_for_update().get(pk=bill_id, C_Company_Code=company_code)
        
        # 2. Capacity Checks
        line_unsettled = recon_line.transaction_amount - recon_line.amount_settled
        if amount_to_apply > (line_unsettled + Decimal('0.0001')):
            messages.error(request, f"Allocation failed: Only R{line_unsettled:.2f} remains.")
            return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)
            
        # 3. Bill Needs Calculation
        bill_settled_agg = BillSettlement.objects.filter(unity_bill_source_id=bill_record.pk).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
        journal_total = JournalEntry.objects.filter(target_bill=bill_record).aggregate(total=Sum('amount'))['total'] or ZERO_DECIMAL
        
        total_commitments = bill_settled_agg + journal_total
        bill_remaining_liability = bill_record.H_Schedule_Amount - total_commitments
        
        # 4. Final Application Amount (Capped by bill liability)
        final_amount_applied = min(amount_to_apply, bill_remaining_liability)
        
        if final_amount_applied <= ZERO_DECIMAL:
            messages.warning(request, "This bill is already fully covered.")
            return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)
            
        # 5. Create Settlement (Audit Trail for the Bill)
        BillSettlement.objects.create(
            reconned_bank_line=recon_line,
            unity_bill_source=bill_record,
            settled_amount=final_amount_applied,
            settlement_date=aware_dt,
            confirmed_by=request.user,
            original_import_bank_id=recon_line.bank_line_id,
        )
        
        # 6. Update Source Line - Record the amount used for this specific bill
        recon_line.amount_settled += final_amount_applied
        
        # 7. HANDLE REMAINDER (Overs Logic)
        # Calculate exactly what is left on the physical bank transaction
        amount_left_on_source = recon_line.transaction_amount - recon_line.amount_settled
        
        if amount_left_on_source > Decimal('0.009'):
            if should_split_and_reallocate:
                # OPTION A: Hard Split to Unassigned Pool
                ReconnedBank.objects.create(
                    bank_line_id=recon_line.bank_line_id,
                    company_code=None,
                    transaction_amount=amount_left_on_source,
                    transaction_date=recon_line.transaction_date,
                    recon_status='Unreconciled - New Source',
                    amount_settled=ZERO_DECIMAL,
                )
                messages.info(request, f"Remainder R{amount_left_on_source:.2f} split to unassigned pool.")
            else:
                # OPTION B: Move to CreditNote (Overs credit line)
                CreditNote.objects.create(
                    member_group_code=company_code,
                    schedule_amount=amount_left_on_source,
                    credit_link_status='Unlinked',
                    link_request_reason="Overs credit line",
                    source_bank_line=recon_line,
                    comment=f"Auto-generated Overs from Bank Line {recon_line.id} on Bill {bill_id}",
                    processed_by=request.user.username,
                    processed_date=aware_dt,
                    ccdates_month=bill_record.A_CCDatesMonth,
                    bank_stmt_date=recon_line.transaction_date,
                    note_selection="OVERS" 
                )
                messages.warning(request, f"R{amount_left_on_source:.2f} moved to Available Credits as 'Overs credit line'.")

            # CRITICAL: Mark the original segment as fully reconciled so it disappears from 'Bank Lines' UI
            # We set the 'transaction_amount' of this segment to what was actually settled here, 
            # because the rest has been moved to a new CreditNote or Bank Segment.
            recon_line.transaction_amount = recon_line.amount_settled
            recon_line.recon_status = 'Reconciled'
        else:
            recon_line.recon_status = 'Reconciled'

        recon_line.save()
        
        messages.success(request, f"Applied R{final_amount_applied:.2f} from Bank Line.")
        return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)
        
    except Exception as e:
        messages.error(request, f"Allocation Error: {str(e)}")
        return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)
    
@login_required
@transaction.atomic
def finalize_reconciliation(request, company_code, bill_id):
    """
    Processes all selected bank line allocations in bulk, then
    finalizes the bill if the balance requirements are met.
    """
    try:
        bill_record = UnityBill.objects.select_for_update().get(pk=bill_id, C_Company_Code=company_code)
        aware_dt = timezone.now()

        # 1. PROCESS BULK ALLOCATIONS (If any checkboxes were checked)
        if request.method == 'POST':
            selected_ids = request.POST.getlist('selected_recon_ids')
            
            for recon_id in selected_ids:
                amount_str = request.POST.get(f'amount_to_apply_{recon_id}')
                if not amount_str:
                    continue
                
                amount_to_apply = Decimal(amount_str)
                if amount_to_apply <= ZERO_DECIMAL:
                    continue

                recon_line = ReconnedBank.objects.select_for_update().get(pk=recon_id)
                
                line_unsettled = recon_line.transaction_amount - recon_line.amount_settled
                applied_amount = min(amount_to_apply, line_unsettled)

                # Create Audit Trail
                BillSettlement.objects.create(
                    reconned_bank_line=recon_line,
                    unity_bill_source=bill_record,
                    settled_amount=applied_amount,
                    settlement_date=aware_dt,
                    confirmed_by=request.user,
                    original_import_bank_id=recon_line.bank_line_id,
                )

                # Update Bank Line
                recon_line.amount_settled += applied_amount
                if recon_line.amount_settled >= (recon_line.transaction_amount - Decimal('0.0001')):
                    recon_line.recon_status = 'Reconciled'
                else:
                    recon_line.recon_status = 'Partially Reconciled'
                recon_line.save()

        # 2. FINALIZATION CHECK (Verify if bill is now balanced)
        bill_settled_agg = BillSettlement.objects.filter(unity_bill_source_id=bill_record.pk).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
        
        if bill_settled_agg >= (bill_record.H_Schedule_Amount - Decimal('0.0001')):
            if not bill_record.is_reconciled:
                bill_record.is_reconciled = True
                bill_record.save()
                messages.success(request, f"Bill #{bill_id} successfully processed and marked as **RECONCILED**.")
                
                # FIX: Redirect to the success view name used in urls.py
                return redirect('reconciliation_success_view', company_code=company_code, bill_id=bill_id)
            else:
                messages.info(request, "Bill is already reconciled.")
        else:
            remaining_liability = bill_record.H_Schedule_Amount - bill_settled_agg
            messages.error(request, f"Processed selected lines, but R{remaining_liability:.2f} still remains. Bill cannot be closed yet.")

        return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)

    except Exception as e:
        messages.error(request, f"Error during finalization: {e}")
        return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)
    
@login_required
def reconciliation_success_view(request, company_code, bill_id):
    """
    Renders the confirmation/final summary page after successful reconciliation.
    Gathers all required context for finalize_reconciliation.html.
    """
    bill_record = get_object_or_404(UnityBill, id=bill_id, C_Company_Code=company_code)
    
    # --- Data Aggregation ---
    
    # 1. Settled Totals (Cash + Credit + Journal)
    total_settled_against_bill = BillSettlement.objects.filter(
        unity_bill_source_id=bill_record.pk
    ).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
    
    total_credit_assigned = BillSettlement.objects.filter(
        unity_bill_source_id=bill_record.pk, 
        source_credit_note_id__isnull=False
    ).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
    
    # 2. Bank Lines used for settlement display
    lines_to_settle = get_bank_lines_used_in_settlement(bill_record) 
    
    # 3. Fiscal Dates calculation
    bill_date = bill_record.A_CCDatesMonth
    month_start_date = bill_date.replace(day=1)
    fiscal_starting_date = month_start_date 
    fiscal_closing_date = month_start_date + relativedelta(months=1) - relativedelta(days=1)
    
    # 4. Final Math for Template Display
    total_scheduled_amount_initial = bill_record.H_Schedule_Amount
    # Remaining liability should be 0, but we use max() to avoid negative display
    scheduled_amount = max(ZERO_DECIMAL, total_scheduled_amount_initial - total_settled_against_bill)
    
    # total_debt represents the total funds applied (total_settled_against_bill)
    total_debt = total_settled_against_bill
    
    # --- Context Setup (Matches finalize_reconciliation.html variables) ---
    context = {
        'company_code': company_code,
        'bill_record': bill_record,
        'lines_to_settle': lines_to_settle, 
        'total_debt': total_debt,
        'total_scheduled_amount_initial': total_scheduled_amount_initial,
        'total_settled_against_bill': total_settled_against_bill,
        'total_credit_assigned': total_credit_assigned,
        'scheduled_amount': scheduled_amount,
        
        'fiscal_starting_date': fiscal_starting_date,
        'fiscal_closing_date': fiscal_closing_date,

        'warning_message': '✅ RECONCILIATION SUCCESSFUL: This bill is permanently closed.', 
        'settle_button_text': 'Reconciliation Complete',
    }
    
    return render(request, 'unity_internal_app/finalize_reconciliation.html', context)
    
@login_required
@transaction.atomic
def edit_bill(request, company_code, bill_id):
    """
    Loads an existing UnityBill record for editing and handles form submission.
    CRITICAL FIX: Prevents R0.00 scheduled bills from being finalized when edited.
    FIX: Corrected redirection logic to manually handle the URL anchor.
    """
    # 1. Fetch the existing bill record
    # Assuming UnityBill is correctly imported
    bill_record = get_object_or_404(
        UnityBill,
        id=bill_id,
        C_Company_Code=company_code
    )
    
    if request.method == 'POST':
        # 2. Bind the form data to the instance
        # Assuming PreBillForm is imported
        form = PreBillForm(request.POST, instance=bill_record)
        
        if form.is_valid():
            # 3. Save the updated instance, but commit=False first to apply custom logic
            edited_bill = form.save(commit=False)
            
            # --- CRITICAL R0.00 CHECK ---
            scheduled_amount = edited_bill.H_Schedule_Amount or ZERO_DECIMAL
            
            if scheduled_amount <= ZERO_DECIMAL:
                # If the scheduled amount is zero, prevent database closure by clearing final dates.
                edited_bill.J_Final_Date = None
                edited_bill.I_Submitted_Date = None
                messages.warning(request, f"Bill #{bill_id} saved, but R0.00 scheduled amount prevents closure. Status remains open.")
            
            # Now save the record with the potentially updated dates
            edited_bill.save()
            
            messages.success(request, f"Bill for {company_code} (ID: {bill_id}) successfully updated.")
            
            # --- FIX: MANUALLY APPEND ANCHOR ---
            # 1. Reverse the URL using only the accepted keyword arguments ('company_code').
            url = reverse('unity_information', kwargs={'company_code': company_code})
            
            # 🛑 CRITICAL FIX: Add cache-busting timestamp to the redirect URL
            timestamp = timezone.now().timestamp()
            
            # 2. Append the anchor string ('#recon') manually.
            return redirect(f"{url}?cache={timestamp}#recon")

        else:
            messages.error(request, "Please correct the errors in the form.")
            
    else:
        # 4. For GET requests, load the form with the existing instance data
        form = PreBillForm(instance=bill_record)

    context = {
        'company_code': company_code,
        'form': form,
        'bill_id': bill_id,
        'is_editing': True,
    }
    
    # Use the generic template
    return render(request, 'unity_internal_app/bill_form.html', context)

# --- Define ALL required Excel headers (Remains the same) ---
EXCEL_FIELD_MAPPING = {
    'CCDates Month': 'ccdates_month',
    'Fund Code': 'fund_code',
    'Member Group Code': 'member_group_code',
    'Member Group Name': 'member_group_name',
    'Active Members - (Info from FuturaSA & NOT checked by Sanlam)': 'active_members',
    'Schedule Date': 'schedule_date',
    'Final Data Received Date': 'final_data_received_date',
    'Schedule Amount': 'schedule_amount',
    'Confirmation Date': 'confirmation_date',
    'Bank Stmt Date': 'bank_stmt_date',
    'Bank Deposit Amount': 'bank_deposit_amount',
    'Allocated Amount (For Front Office use & not to be checked by Sanlam)': 'allocated_amount',
    'Comment': 'comment',
    'Receipt In Live': 'receipt_in_live',
    'Receipting done by': 'receipting_done_by',
    '0101 Balance Sufficnt: Yes/No': 'balance_sufficient_flag',
    'Date & Letter checked:': 'date_letter_checked',
    'Done by:': 'done_by',
}
# ----------------------------------------------------

# --- HELPER FUNCTIONS (MUST BE DEFINED BEFORE import_credit) ---
# ----------------------------------------------------
def clean_value(value):
    """Cleans and strips white space from a value."""
    if value is None:
        return ''
    return str(value).strip()

# CORRECTED parse_date function (Around line 1060)
def parse_date(date_obj):
    """
    Handles parsing date strings or datetime/date objects.
    Returns a Python datetime.date object or None.
    """
    if date_obj is None or date_obj == '':
        return None
    
    # 1. Handle Python datetime/date objects
    if isinstance(date_obj, datetime):
        return date_obj.date()
    if isinstance(date_obj, date): # <--- Checks against the imported 'date' class
        return date_obj
    
    # 2. Convert value to clean string
    date_str = str(date_obj).strip()
    date_str = date_str.split(' ')[0] # Strip off any time component
    
    # 3. Try common formats
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y%m%d'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
            
    return None

def parse_decimal(amount_str):
    """Cleans and converts string to Decimal."""
    if amount_str is None or amount_str == '':
        return None
    cleaned = str(amount_str).replace('R', '').replace(',', '').strip()
    try:
        if not cleaned: return None
        return Decimal(cleaned)
    except Exception:
        return None

# ----------------------------------------------------
# --- IMPORT_CREDIT FUNCTION (Calls the helpers above) ---
# ----------------------------------------------------
@login_required
@transaction.atomic
def import_credit(request):
    if request.method != 'POST' or 'credit_file' not in request.FILES:
        return render(request, 'unity_internal_app/import_credit.html', {'expected_headers': EXCEL_FIELD_MAPPING.keys()})
        
    credit_file = request.FILES['credit_file']
    filename = credit_file.name
    rows = []
    
    # 1. DETERMINE READER METHOD AND READ FILE DATA (Logic unchanged)
    if filename.endswith(('.xlsx', '.xls')):
        # XLSX/XLS: Use openpyxl to read
        try:
            from openpyxl import load_workbook
            workbook = load_workbook(credit_file)
            sheet = workbook.active
            rows = [[clean_value(cell.value) for cell in row] for row in sheet.iter_rows()]
            
            if len(rows) > 4:
                rows = rows[4:]
            else:
                messages.error(request, "Excel file too short. Cannot skip the first 4 rows.")
                return redirect('import_credit')
                
        except Exception as e:
            messages.error(request, f"Error reading Excel file: {e}")
            return redirect('import_credit')
    
    elif filename.endswith('.csv'):
        # CSV: Use standard CSV reader
        try:
            file_data = credit_file.read().decode('utf-8')
            io_string = io.StringIO(file_data)
            
            try:
                import csv
                dialect = csv.Sniffer().sniff(io_string.readline())
                io_string.seek(0)
                reader = csv.reader(io_string, dialect)
            except Exception:
                io_string.seek(0)
                reader = csv.reader(io_string, delimiter=',')
                
            all_csv_rows = list(reader)

            if len(all_csv_rows) > 4:
                rows = all_csv_rows[4:]
            else:
                messages.error(request, "CSV file too short. Cannot skip the first 4 rows.")
                return redirect('import_credit')
                
        except UnicodeDecodeError:
            messages.error(request, "Unicode Decode Error: The CSV file is not encoded in UTF-8. Try saving it as CSV (Comma delimited) with UTF-8 encoding.")
            return redirect('import_credit')
        except Exception as e:
            messages.error(request, f"Error reading CSV file: {e}")
            return redirect('import_credit')
    
    else:
        messages.error(request, "Invalid file format. Please upload an Excel (.xlsx/.xls) or CSV file.")
        return redirect('import_credit')
    
    if not rows:
        messages.error(request, "No data rows found after skipping template headers.")
        return redirect('import_credit')

    # 2. READ HEADER (Logic unchanged)
    try:
        header = rows.pop(0)
        column_indices = {}
        
        for excel_header, target_field in EXCEL_FIELD_MAPPING.items():
            try:
                index = header.index(excel_header)
                column_indices[target_field] = index
            except ValueError:
                column_indices[target_field] = None
        
        if column_indices.get('member_group_code') is None:
            messages.error(request, f"Import failed: Mandatory column 'Member Group Code' is missing from the effective header row (Row 5 in the file).")
            return redirect('import_credit')
    except Exception as e:
        messages.error(request, f"Error during header processing: {e}")
        return redirect('import_credit')


    # 3. PROCESS ROWS (Using single saves and strict field type checking)
    rows_processed = 0
    
    # Get the CreditNote model's field map once for efficiency
    credit_note_fields = {f.name: f for f in CreditNote._meta.fields}

    try:
        with transaction.atomic():
            for row in rows:
                if not any(row) or len(row) < len(header):
                    continue
                
                row_data = {}
                has_error = False
                
                for target_field, index in column_indices.items():
                    if index is not None and index < len(row):
                        raw_value = row[index]
                        
                        # --- Type-specific parsing and ASSIGNMENT ---
                        if target_field in credit_note_fields:
                            field_instance = credit_note_fields[target_field]
                            
                            if isinstance(field_instance, DateField):
                                parsed_date = parse_date(raw_value)
                                
                                # Explicitly format to YYYY-MM-DD string only if parsed
                                if parsed_date:
                                    row_data[target_field] = parsed_date.strftime('%Y-%m-%d')
                                else:
                                    row_data[target_field] = None
                                    
                            elif isinstance(field_instance, DateTimeField):
                                # If you had DATETIME fields from Excel, parse them here
                                row_data[target_field] = None
                            
                            elif 'amount' in target_field or target_field == 'schedule_amount':
                                row_data[target_field] = parse_decimal(raw_value)
                            
                            elif target_field == 'active_members':
                                try:
                                    row_data[target_field] = int(clean_value(raw_value))
                                except ValueError:
                                    row_data[target_field] = None
                                    
                            else:
                                row_data[target_field] = clean_value(raw_value)
                        
                    else:
                        row_data[target_field] = None
                    
                    if target_field == 'member_group_code' and not row_data.get('member_group_code'):
                        messages.warning(request, f"Skipping row {rows_processed + 1}: Missing mandatory 'Member Group Code'.")
                        has_error = True
                        break
                
                if has_error:
                    continue

                # Handle processed_date (The only DATETIME field in your target table)
                # 🛠️ CRITICAL FIX APPLIED HERE: Using datetime.now() instead of datetime.datetime.now()
                row_data['processed_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                row_data['processed_by'] = request.user.username
                
                # --- Create the object ---
                CreditNote.objects.create(**row_data)
                
                rows_processed += 1
            
        if rows_processed > 0:
            messages.success(request, f"Successfully imported {rows_processed} Bill Detail Records into Credit_note.")
        else:
            messages.warning(request, "No valid records found to import.")
            
    except Exception as e:
        messages.error(request, f"A critical database error occurred during single insertion (Row {rows_processed + 1}): {e}")
        
    return redirect('import_credit')

@login_required
def credit_note_list(request):
    """
    Displays all imported CreditNote records.
    Records disappear from this global list as soon as a 
    user initiates a request (Status moves away from Unlinked).
    """
    # Show only the 'Inbox' of items that have NO pending or approved allocations
    credit_notes = CreditNote.objects.filter(
        credit_link_status='Unlinked'
    ).order_by('-processed_date')
    
    context = {
        'page_title': 'Available Credit Imports',
        'credit_notes': credit_notes,
    }
    
    return render(request, 'unity_internal_app/credit_note_list.html', context)

@login_required
@transaction.atomic
def assign_fiscal_date_view(request, note_id):
    from django.contrib import messages
    from django.shortcuts import redirect, get_object_or_404, render
    from django.urls import reverse
    from django.utils import timezone
    from decimal import Decimal
    from .models import CreditNote, UnityBill
    from .forms import FiscalDateAssignmentForm

    context_type = request.GET.get('context', 'info')
    note_record = get_object_or_404(CreditNote, id=note_id)
    current_company_code = note_record.member_group_code 

    if request.method == 'POST':
        form = FiscalDateAssignmentForm(request.POST, instance=note_record)
        if 'fiscal_date' in form.fields: form.fields['fiscal_date'].required = False
        if 'target_bill_id' in form.fields: form.fields['target_bill_id'].required = False

        new_group_code = request.POST.get('member_group_code')
        link_reason = request.POST.get('link_reason')
        requested_amt = request.POST.get('requested_link_amount') # Capture specific amount

        if form.is_valid() and new_group_code:
            note = form.save(commit=False)
            note.member_group_code = new_group_code
            
            # Store the specific amount requested for the manager to see
            if requested_amt:
                note.requested_amount = Decimal(requested_amt)
            
            open_bill = UnityBill.objects.filter(
                C_Company_Code=new_group_code,
                is_reconciled=False
            ).order_by('A_CCDatesMonth').first()
            
            if open_bill:
                note.pending_linked_bill = open_bill
                note.link_request_reason = link_reason
                note.credit_link_status = 'Pending'
                note.save()
                messages.success(request, f"Requested R{note.requested_amount} allocation for Bill #{open_bill.id}.")
            else:
                note.save()
                messages.warning(request, f"Code updated, but NO open bill found.")

            timestamp = timezone.now().timestamp()
            return redirect(f"{reverse('unity_billing_history', kwargs={'company_code': new_group_code})}?cache={timestamp}#credit")
    else:
        form = FiscalDateAssignmentForm(instance=note_record)

    context = {'page_title': 'Request Link Approval', 'note': note_record, 'form': form, 'company_code': current_company_code}
    return render(request, 'unity_internal_app/assign_fiscal_date.html', context)

@login_required
@transaction.atomic
def allocate_surplus_to_bill(request, bill_id):
    """
    Process the allocation of a Surplus to a Bill via a Journal Entry.
    UPDATED: Now triggers is_reconciled = True if the allocation completes the bill.
    """
    # Ensure local imports are available inside the function or globally
    from django.db.models import Sum
    from decimal import Decimal
    from django.utils import timezone
    from datetime import datetime

    if request.method != 'POST':
        return redirect('dashboard')

    # 1. Get Data from POST
    surplus_id = request.POST.get('surplus_id')
    amount_str = request.POST.get('amount')
    
    target_bill = get_object_or_404(UnityBill, pk=bill_id)
    company_code = target_bill.C_Company_Code
    
    try:
        amount_to_allocate = Decimal(amount_str)
        if amount_to_allocate <= ZERO_DECIMAL:
            raise ValueError("Amount must be positive.")

        # --- Fetch Surplus and Validate ---
        surplus = ScheduleSurplus.objects.select_for_update().get(pk=surplus_id)
        
        # Check if enough remains (DB level check)
        used_so_far = JournalEntry.objects.filter(surplus_source=surplus).aggregate(sum=Sum('amount'))['sum'] or ZERO_DECIMAL
        remaining_surplus = surplus.surplus_amount - used_so_far

        if amount_to_allocate > remaining_surplus:
            messages.error(request, f"Cannot allocate R{amount_to_allocate}. Only R{remaining_surplus} remains in this surplus.")
            return redirect(reverse('pre_bill_reconciliation_summary', kwargs={'company_code': company_code, 'bill_id': bill_id}))

        current_date_obj = timezone.now().date()
        naive_dt = datetime.combine(current_date_obj, datetime.min.time())
        aware_dt = timezone.make_aware(naive_dt)

        # 1. Create the Journal Entry
        journal_entry = JournalEntry.objects.create(
            surplus_source=surplus,
            target_bill=target_bill,
            amount=amount_to_allocate,
            created_by=request.user.username,
            allocation_date=current_date_obj
        )
        
        # 2. Create the BillSettlement record
        BillSettlement.objects.create(
            reconned_bank_line=None,
            unity_bill_source=target_bill,
            settled_amount=amount_to_allocate,
            settlement_date=aware_dt,
            source_credit_note_id=None,
            source_journal_entry_id=journal_entry.pk
        )
        
        # 3. Update Surplus Status
        new_used_amount = used_so_far + amount_to_allocate
        
        if new_used_amount >= surplus.surplus_amount:
            surplus.status = 'FULLY_APPLIED'
        else:
            surplus.status = 'PARTIALLY_APPLIED'
        surplus.save()

        # ============================================================
        # --- NEW LOGIC: CHECK FOR BILL COMPLETION (THE TRIGGER) ---
        # ============================================================
        
        # Calculate total paid so far (Cash + Credits + Journals)
        total_settled = BillSettlement.objects.filter(
            unity_bill_source_id=target_bill.pk
        ).aggregate(t=Sum('settled_amount'))['t'] or ZERO_DECIMAL
        
        # Check if bill is fully paid
        if total_settled >= target_bill.H_Schedule_Amount:
            target_bill.is_reconciled = True  # <--- FLIP THE SWITCH
            target_bill.save()
            messages.success(request, f"Allocation successful. Bill #{target_bill.id} is now FULLY RECONCILED.")
        else:
            messages.success(request, f"Journal Entry created! R{amount_to_allocate} allocated. Bill remains OPEN.")

    except Exception as e:
        messages.error(request, f"Allocation failed: {str(e)}")

    # Redirect
    timestamp = timezone.now().timestamp()
    return redirect(f"{reverse('pre_bill_reconciliation_summary', kwargs={'company_code': company_code, 'bill_id': bill_id})}?cache={timestamp}")

@login_required
def settle_bill_report(request, company_code, bill_id):
    """
    Read-only Audit Report for a settled bill.
    FIX: Attaches the full CreditNote object to the BillSettlement record 
         to supply the necessary details (like Import Date and Review Note) 
         to the audit report template.
    """
    from decimal import Decimal
    from django.db.models import Sum
    from django.shortcuts import get_object_or_404, render
    from .models import UnityBill, BillSettlement, CreditNote, JournalEntry, ScheduleSurplus # Ensure models are imported

    bill_record = get_object_or_404(UnityBill, id=bill_id, C_Company_Code=company_code)
    
    # 1. Fetch CASH Settlements (where reconned_bank_line is NOT NULL)
    settlements = BillSettlement.objects.filter(
        unity_bill_source_id=bill_record.id,
        reconned_bank_line_id__isnull=False,
    ).select_related('reconned_bank_line', 'reconned_bank_line__bank_line').order_by('settlement_date')
    
    settled_total = sum(s.settled_amount for s in settlements)

    # 2. Fetch CREDIT Settlements (where source_credit_note_id is NOT NULL)
    credit_settlements = BillSettlement.objects.filter(
        unity_bill_source_id=bill_record.id,
        source_credit_note_id__isnull=False
    ).order_by('settlement_date')
    
    credit_total = sum(c.settled_amount or ZERO_DECIMAL for c in credit_settlements)

    # 3. ATTACH CREDIT NOTE DETAILS (CRITICAL NEW LOGIC)
    
    # Get all CreditNote IDs involved in the settlements
    credit_ids = [s.source_credit_note_id for s in credit_settlements if s.source_credit_note_id is not None]
    
    # Fetch all relevant CreditNote objects in one query and map them
    credit_note_map = {
        cn.id: cn for cn in CreditNote.objects.filter(id__in=credit_ids)
    }
    
    # Attach the full CreditNote object to the BillSettlement record
    for settlement in credit_settlements:
        settlement.original_credit_note = credit_note_map.get(settlement.source_credit_note_id)

    # 4. Fetch SURPLUS Settlements (where source_journal_entry_id is NOT NULL)
    journal_settlements = BillSettlement.objects.filter(
        unity_bill_source_id=bill_record.id,
        source_journal_entry_id__isnull=False
    ).order_by('settlement_date')

    journal_total = sum(j.settled_amount or ZERO_DECIMAL for j in journal_settlements)

    # 5. Grand Total Paid
    total_paid = settled_total + credit_total + journal_total
    
    # 6. Check for Surplus Generated
    generated_surplus = ScheduleSurplus.objects.filter(unity_bill_source_id=bill_record.id).first()

    context = {
        'bill': bill_record,
        'company_code': company_code,
        
        # Data Lists
        'settlements': settlements,
        'credit_settlements': credit_settlements, # <-- Now includes the attached original_credit_note
        'journal_settlements': journal_settlements,
        'generated_surplus': generated_surplus,
        
        # Totals
        'settled_total': settled_total,
        'credit_total': credit_total,
        'journal_total': journal_total,
        'total_paid': total_paid,
        'zero': ZERO_DECIMAL
    }
    
    return render(request, 'unity_internal_app/settle_bill_report.html', context)

from django.http import HttpResponse
@login_required
def export_settled_bill_csv(request, company_code, bill_id):
    """
    Exports the SINGLE settled bill details to a CSV file.
    """
    bill = get_object_or_404(UnityBill, id=bill_id, C_Company_Code=company_code)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Settled_Bill_{company_code}_{bill_id}.csv"'

    writer = csv.writer(response)
    
    headers = [
        'A_CCDatesMonth', 'B_Fund_Code', 'C_Company_Code', 'D_Company_Name',
        'E_Active_Members', 'F_Pre-Bill_Date', 'G_Schedule_Date', 'H_Schedule_Amount',
        'I_Submitted_Date', 'J_Final_Date', 'K_Bank_Stmt_Date', 'L_Bank_Deposit_Amount'
    ]
    writer.writerow(headers)

    def write_row(date_val, amount_val):
        writer.writerow([
            bill.A_CCDatesMonth, bill.B_Fund_Code, bill.C_Company_Code, bill.D_Company_Name,
            bill.E_Active_Members, bill.F_Pre_Bill_Date, bill.G_Schedule_Date, bill.H_Schedule_Amount,
            bill.I_Submitted_Date, bill.J_Final_Date,
            date_val, amount_val
        ])

    # 1. Bank Settlements
    settlements = BillSettlement.objects.filter(unity_bill_source_id=bill.id).select_related('reconned_bank_line__bank_line')
    for s in settlements:
        # Need to check if reconned_bank_line is not None (credit/journal settlements won't have it)
        if s.reconned_bank_line:
            write_row(s.reconned_bank_line.bank_line.date if s.reconned_bank_line.bank_line else s.settlement_date.date(), s.settled_amount)

    # 2. Credit Notes (redundant if using BillSettlement, but retained for old CreditNote model lookup)
    credits = CreditNote.objects.filter(assigned_unity_bill=bill)
    for c in credits:
        write_row(c.fiscal_date or c.processed_date, c.schedule_amount)

    # 3. Journal Entries
    journals = JournalEntry.objects.filter(target_bill=bill)
    for j in journals:
        write_row(j.allocation_date, j.amount)

    return response

# Assuming UnityBill model and other necessary imports exist.
# MAX_DEPOSITS constant
MAX_DEPOSITS = 5
TWO_PLACES = Decimal('0.00') # Assuming this is correctly defined globally

@login_required
def export_global_history_csv(request):
    """
    Exports the payment history for Bills that had settlement activity 
    in a horizontal format (pivoted deposits).
    
    FIX: Unifies data fetching by querying BillSettlement, CreditNote, and 
          JournalEntry models separately and merging the results before pivoting.
    """
    # --- Constants ---
    MAX_DEPOSITS = 5
    TWO_PLACES = Decimal('0.00')
    
    # --- Date Filtering Logic (Unchanged) ---
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    filter_start_date = None
    filter_end_date = None
    
    try:
        if start_date_str:
            filter_start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            filter_end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse("Invalid date format provided for filtering.", status=400)
    
    T1_TABLE = 'bill_settlement'
    
    # --- 1. Determine Bill IDs to Display (Filtered by Settlement Date) ---
    # This logic is kept concise, relying on BillSettlement for date filtering if requested.
    
    all_bills_queryset = UnityBill.objects.all()
    
    if filter_start_date or filter_end_date:
        # Get bill IDs from BillSettlement based on date range
        settlement_filter = BillSettlement.objects.all()
        if filter_start_date:
            settlement_filter = settlement_filter.filter(settlement_date__gte=filter_start_date)
        if filter_end_date:
            settlement_filter = settlement_filter.filter(settlement_date__lte=filter_end_date)
        
        filtered_bill_ids = settlement_filter.values_list('unity_bill_source_id', flat=True).distinct()
        
        if not filtered_bill_ids:
            all_bills_queryset = UnityBill.objects.none()
        else:
            all_bills_queryset = all_bills_queryset.filter(id__in=filtered_bill_ids)
            
    all_bills = list(all_bills_queryset.order_by('C_Company_Code', '-A_CCDatesMonth'))
    filtered_bill_ids = [bill.id for bill in all_bills]
    
    # --- 2. Fetch ALL Granular Settlements (Cash, Credit, Journal) ---

    deposits_by_bill = defaultdict(list)
    credits_map = defaultdict(Decimal)

    if filtered_bill_ids:
        # A. Fetch ALL BillSettlement records for the target bills
        all_settlements = BillSettlement.objects.filter(
            unity_bill_source_id__in=filtered_bill_ids
        ).select_related(
            'reconned_bank_line',
            'reconned_bank_line__bank_line'
        ).order_by('settlement_date')

        # B. Fetch all relevant Credit Notes and Journals for lookups
        credit_ids = all_settlements.values_list('source_credit_note_id', flat=True).distinct()
        journal_ids = all_settlements.values_list('source_journal_entry_id', flat=True).distinct()

        # Optimize: Pre-fetch source object maps (if necessary for rich detail)
        credit_note_details = {cn.id: cn for cn in CreditNote.objects.filter(id__in=credit_ids)}
        journal_entry_details = {je.id: je for je in JournalEntry.objects.filter(id__in=journal_ids)}
        
        # C. Map BillSettlement entries to deposits_by_bill list
        for s in all_settlements:
            deposit_amount = s.settled_amount or ZERO_DECIMAL
            source_type = 'Unknown'
            deposit_date = s.settlement_date.date() # Default date

            if s.reconned_bank_line_id:
                # 1. Cash Settlement (Primary Source is ReconnedBank/ImportBank)
                source_type = 'Cash'
                if s.reconned_bank_line and s.reconned_bank_line.bank_line:
                    deposit_date = s.reconned_bank_line.bank_line.date
            
            elif s.source_credit_note_id:
                # 2. Credit Settlement
                source_type = 'Credit'
                credits_map[s.unity_bill_source_id] += deposit_amount # Track total credit for status check
                
                cn = credit_note_details.get(s.source_credit_note_id)
                if cn and cn.fiscal_date:
                    deposit_date = cn.fiscal_date
            
            elif s.source_journal_entry_id:
                # 3. Journal/Surplus Settlement
                source_type = 'Journal'
                
                je = journal_entry_details.get(s.source_journal_entry_id)
                if je and je.allocation_date:
                    deposit_date = je.allocation_date

            deposits_by_bill[s.unity_bill_source_id].append({
                'date': deposit_date,
                'amount': deposit_amount,
                'type': source_type
            })

    # --- 3. Generate CSV Response ---

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Global_Horizontal_Payments_DOWNLOAD.csv"'

    writer = csv.writer(response)
    
    # 1. Define Headers (Unchanged)
    base_headers = [
        'A_CCDatesMonth', 'B_Fund_Code', 'C_Company_Code', 'D_Company_Name',
        'E_Active_Members', 'F_Pre-Bill_Date', 'G_Schedule_Date', 'H_Schedule_Amount',
        'I_Submitted_Date', 'J_Final_Date',
    ]
    
    payment_headers = []
    for i in range(MAX_DEPOSITS):
        payment_headers.extend([
            f'{chr(75 + 2 * i)}_Bank_Stmt_Date',  # K, M, O, Q, S
            f'{chr(76 + 2 * i)}_Bank_Deposit_Amount'  # L, N, P, R, T
        ])
    
    writer.writerow(base_headers + payment_headers)
    
    # Date format for CSV output
    CSV_DATE_FORMAT = '%d/%m/%Y'

    for bill in all_bills:
        
        deposits = deposits_by_bill.get(bill.id, [])
        
        # Calculate settlement status (CRITICAL: Needs to rely on total paid vs schedule)
        total_settled = sum((d['amount'] for d in deposits), start=TWO_PLACES)
        
        is_settled = total_settled >= (bill.H_Schedule_Amount or TWO_PLACES)

        # CRITICAL FILTER: Skip row if the bill is not fully RECONCILED (as requested)
        if not is_settled:
            continue

        # A. Gather Base Bill Data (Columns A-J)
        row_data = [
            bill.A_CCDatesMonth.strftime(CSV_DATE_FORMAT) if bill.A_CCDatesMonth else '',
            bill.B_Fund_Code or '',
            bill.C_Company_Code or '',
            bill.D_Company_Name or '',
            bill.E_Active_Members or 0,
            bill.F_Pre_Bill_Date.strftime(CSV_DATE_FORMAT) if bill.F_Pre_Bill_Date else '',
            bill.G_Schedule_Date.strftime(CSV_DATE_FORMAT) if bill.G_Schedule_Date else '',
            str((bill.H_Schedule_Amount or ZERO_DECIMAL).quantize(TWO_PLACES)),
            bill.I_Submitted_Date.strftime(CSV_DATE_FORMAT) if bill.I_Submitted_Date else '',
            bill.J_Final_Date.strftime(CSV_DATE_FORMAT) if bill.J_Final_Date else '',
        ]
        
        # B. Prepare for Payment Data (Dynamic Columns K-T)
        payment_data = [''] * (MAX_DEPOSITS * 2)
        
        # Sort all deposits (Cash, Credit, Journal) by date
        deposits.sort(key=lambda d: d['date'])

        for i in range(MAX_DEPOSITS):
            if i < len(deposits):
                deposit = deposits[i]
                
                date_col_index = i * 2
                amount_col_index = i * 2 + 1
                
                # Fill payment data array
                payment_data[date_col_index] = deposit['date'].strftime(CSV_DATE_FORMAT)
                payment_data[amount_col_index] = str(deposit['amount'].quantize(TWO_PLACES))

        # C. Write the final row
        writer.writerow(row_data + payment_data)

    return response

# --- DEFINE CONSTANTS ---
# ZERO_DECIMAL already defined globally at the top
# Tolerance to handle floating point errors when comparing Decimal amounts to zero
TOLERANCE = Decimal('0.00001')

@login_required
def global_history_overview(request):
    """
    Renders a high-level overview of ALL Reconciled Bill History.
    UPDATED: 
    1. Only shows reconciled bills (is_reconciled=True).
    2. Excludes empty/placeholder bills (0 members or 0 amount).
    """
    from decimal import Decimal
    from collections import defaultdict
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    filter_start_date = None
    filter_end_date = None
    ZERO_DECIMAL = Decimal('0.00')
    
    try:
        if start_date_str:
            filter_start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            filter_end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Invalid date format provided for filtering.")
        
    T1_TABLE = 'bill_settlement'
    filtered_bill_ids = set()

    # --- 1. Base Query with Strict Filters ---
    # We apply the filters here first to ensure we only look for settled IDs 
    # belonging to "Valid" reconciled bills.
    base_bills = UnityBill.objects.filter(
        is_reconciled=True
    ).exclude(
        E_Active_Members=0
    ).exclude(
        H_Schedule_Amount=0
    )

    # --- 2. Determine Bill IDs to Display (Filtering by Date) ---
    if filter_start_date or filter_end_date:
        # 1A. Filter by Cash Settlement Date
        where_conditions_cash = []
        sql_args_cash = []
        if filter_start_date:
            where_conditions_cash.append("settlement_date >= %s")
            sql_args_cash.append(filter_start_date)
        if filter_end_date:
            where_conditions_cash.append("settlement_date <= %s")
            sql_args_cash.append(filter_end_date)
            
        where_clause_cash = "WHERE " + " AND ".join(where_conditions_cash) if where_conditions_cash else ""
        cash_filter_sql = f"SELECT DISTINCT unity_bill_source_id FROM {T1_TABLE} {where_clause_cash}"
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(cash_filter_sql, sql_args_cash)
                cash_ids = [row[0] for row in cursor.fetchall()]
                filtered_bill_ids.update(cash_ids)
        except Exception as e:
            messages.error(request, f"Database Error during cash filter: {e}")
            
        # 1B. Filter by Journal Entry Date
        journal_queryset = JournalEntry.objects.all()
        if filter_start_date:
            journal_queryset = journal_queryset.filter(allocation_date__gte=filter_start_date)
        if filter_end_date:
            journal_queryset = journal_queryset.filter(allocation_date__lte=filter_end_date)
        journal_ids = journal_queryset.values_list('target_bill_id', flat=True).distinct()
        filtered_bill_ids.update(journal_ids)
        
        # Apply the found IDs to our base strictly-filtered queryset
        all_bills_queryset = base_bills.filter(id__in=list(filtered_bill_ids))
    else:
        # No date filter: Show all strictly-filtered reconciled bills
        all_bills_queryset = base_bills

    # Prefetch data
    all_bills = list(all_bills_queryset.order_by('-A_CCDatesMonth', 'C_Company_Code'))
    final_bill_ids = [bill.id for bill in all_bills]
    
    # --- 3. Fetch Granular Settlements ---
    final_records = []
    if final_bill_ids:
        id_placeholders = ', '.join(['%s'] * len(final_bill_ids))
        T2_TABLE = 'reconned_bank'
        T3_TABLE = 'importbank'

        # 3A. Cash Deposits
        sql_query_cash = f"""
        SELECT T1.unity_bill_source_id, T3.DATE, T1.settled_amount
        FROM {T1_TABLE} T1
        LEFT JOIN {T2_TABLE} T2 ON T1.reconned_bank_line_id = T2.bank_line_id
        LEFT JOIN {T3_TABLE} T3 ON T2.bank_line_id = T3.id
        WHERE T1.unity_bill_source_id IN ({id_placeholders})
        """
        deposits_by_bill = defaultdict(list)
        
        with connection.cursor() as cursor:
            cursor.execute(sql_query_cash, final_bill_ids)
            for row in cursor.fetchall():
                if row[1]: # Only if deposit_date exists
                    deposits_by_bill[row[0]].append({'date': row[1], 'amount': row[2], 'type': 'Cash'})
            
        # 3B. Journal Entries
        journal_queryset = JournalEntry.objects.filter(target_bill__in=final_bill_ids)
        for je in journal_queryset:
            deposits_by_bill[je.target_bill_id].append({
                'date': je.allocation_date,
                'amount': je.amount,
                'type': 'Journal',
            })
            
        # 3C. Credits
        credit_notes_agg = BillSettlement.objects.filter(
            unity_bill_source_id__in=final_bill_ids,
            source_credit_note_id__isnull=False
        ).values('unity_bill_source_id').annotate(total_credit=Sum('settled_amount'))
        credits_map = {item['unity_bill_source_id']: item['total_credit'] for item in credit_notes_agg}
    
        # --- 4. Final Consolidation ---
        for bill in all_bills:
            deposits = deposits_by_bill.get(bill.id, [])
            cash_journal_settled = sum((d['amount'] for d in deposits), start=ZERO_DECIMAL)
            credit_settled = credits_map.get(bill.id, ZERO_DECIMAL)
            
            final_records.append({
                'bill': bill,
                'deposits': deposits,
                'status_name': 'RECON COMPLETE',
                'status_class': 'badge-success',
                'is_settled': True,
                'total_settled': cash_journal_settled + credit_settled,
            })

    context = {
        'bill_records': final_records,
        'filter_start_date': filter_start_date.strftime('%Y-%m-%d') if filter_start_date else '',
        'filter_end_date': filter_end_date.strftime('%Y-%m-%d') if filter_end_date else '',
    }
    return render(request, 'unity_internal_app/global_history_overview.html', context)

@login_required
def unallocate_surplus(request, bill_id):
    if request.method == 'POST':
        # Retrieve necessary data from the POST request
        journal_id = request.POST.get('journal_entry_id')
        company_code = request.POST.get('company_code') 
        
        # Default redirect in case of missing data
        if not journal_id or not company_code:
            messages.error(request, "Error: Journal Entry ID or Company Code is missing.")
            return redirect('pre_bill_reconciliation_summary', company_code=company_code or 'DEFAULT', bill_id=bill_id)

        try:
            with transaction.atomic():
                # 1. Fetch the Journal Entry (e.g., ID 16 or 17 in your example)
                journal_entry = get_object_or_404(
                    JournalEntry, 
                    pk=journal_id, 
                    target_bill_id=bill_id
                )
                amount = journal_entry.amount
                
                # 2. Find and delete the corresponding BillSettlement record.
                # This record reduces the bill's schedule/total_applied metric.
                settlement_record = get_object_or_404(
                    BillSettlement,
                    source_journal_entry_id=journal_entry.pk,
                    unity_bill_source_id=bill_id
                )
                settlement_record.delete()
                
                # 3. Delete the Journal Entry.
                # This releases the surplus funds back into the available pool.
                journal_entry.delete()
            
            messages.success(request, f"Journal Entry successfully reversed. R{amount:.2f} unallocated from Bill #{bill_id}.")

        except BillSettlement.DoesNotExist:
            messages.error(request, f"Error: BillSettlement record for Journal #{journal_id} not found. Metrics may be inconsistent.")
        except JournalEntry.DoesNotExist:
            messages.error(request, f"Error: Journal Entry #{journal_id} not found or does not belong to this bill.")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred during reversal: {e}")

    # Redirect back to the summary page using the correct company code
    return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)

@login_required
def confirmations_view(request):
    """
    Displays bills ready for daily confirmation review.
    
    UPDATED: 
    1. Only shows reconciled bills (is_reconciled=True).
    2. Filters out empty/placeholder bills (0 members or 0 amount).
    """
    from decimal import Decimal
    
    # 1. Date Filtering
    filter_start_date_str = request.GET.get('start_date')
    filter_end_date_str = request.GET.get('end_date')

    # Base Query: Order by 'Final Date' (Ascending), then 'Company Code'
    bills_queryset = UnityBill.objects.all().order_by('J_Final_Date', 'C_Company_Code')
    
    # --- NEW FILTERS ---
    # Only include bills that are fully reconciled/closed
    # AND exclude bills with 0 members or 0 schedule amount to hide "N/A" or empty data
    bills_queryset = bills_queryset.filter(
        is_reconciled=True
    ).exclude(
        E_Active_Members=0
    ).exclude(
        H_Schedule_Amount=0
    )

    if filter_start_date_str:
        try:
            start_dt = datetime.strptime(filter_start_date_str, '%Y-%m-%d').date()
            bills_queryset = bills_queryset.filter(J_Final_Date__gte=start_dt)
        except ValueError:
            pass

    if filter_end_date_str:
        try:
            end_dt = datetime.strptime(filter_end_date_str, '%Y-%m-%d').date()
            bills_queryset = bills_queryset.filter(J_Final_Date__lte=end_dt)
        except ValueError:
            pass
            
    # Limit to top 50 for performance
    review_bills = bills_queryset[:50]

    # 2. Data Consolidation
    confirmation_data = []
    
    for bill in review_bills:
        settlements = BillSettlement.objects.filter(unity_bill_source_id=bill.pk).order_by('settlement_date')
        source_details = []
        active_members = bill.E_Active_Members or 0 
        
        for settlement in settlements:
            source = {}
            source['amount'] = settlement.settled_amount 

            if settlement.reconned_bank_line:
                bank_line = settlement.reconned_bank_line
                source['date'] = bank_line.transaction_date
                source['type'] = 'Bank Line'
            elif settlement.source_credit_note_id:
                try:
                    credit_note = CreditNote.objects.get(id=settlement.source_credit_note_id)
                    source['date'] = credit_note.bank_stmt_date or settlement.settlement_date.date()
                    source['type'] = 'Credit Note'
                except Exception:
                    source['date'] = settlement.settlement_date.date()
                    source['type'] = 'Credit Note (Source Missing)'
            else:
                source['date'] = settlement.settlement_date.date()
                source['type'] = 'Other Source'

            source_details.append(source)
            
        source_details.sort(key=lambda x: x['date'] if x['date'] else datetime.date(1900, 1, 1))

        schedule_amount = bill.H_Schedule_Amount if bill.H_Schedule_Amount is not None else 0 

        confirmation_data.append({
            'bill_id': bill.id,
            'cc_dates_month': bill.A_CCDatesMonth,
            'company_code': bill.C_Company_Code,
            'active_members': active_members, 
            'schedule_date': bill.A_CCDatesMonth, 
            'final_date': bill.J_Final_Date or None, 
            'schedule_amount': schedule_amount,
            'confirmed_date': settlements.first().settlement_date.date() if settlements.exists() else None,
            'source_details': source_details,
        })

    # =========================================================
    # EXPORT TO EXCEL LOGIC (CLEAN GROUPED LAYOUT)
    # =========================================================
    if request.GET.get('export_excel'):
        import openpyxl
        from openpyxl.styles import Font, Alignment
        from django.http import HttpResponse

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Confirmations"

        headers = [
            'CC Dates Month', 'Company Code', 'Active Members', 
            'Schedule Date', 'Final Date', 'Schedule Amount', 
            'Confirmed Date', 'Bank Date', 'Bank Amount'
        ]
        ws.append(headers)

        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')

        for item in confirmation_data:
            bill_common = [
                item['cc_dates_month'],          
                item['company_code'],          
                item['active_members'],          
                item['schedule_date'],         
                item['final_date'],            
                item['schedule_amount'],         
                item['confirmed_date'],          
            ]

            empty_common = [''] * len(bill_common)
            sources = item['source_details']

            if not sources:
                ws.append(bill_common + ['', '']) 
            else:
                for index, source in enumerate(sources):
                    bank_cols = [
                        source['date'],
                        source['amount']
                    ]
                    
                    if index == 0:
                        ws.append(bill_common + bank_cols)
                    else:
                        ws.append(empty_common + bank_cols)

        filename = f"Daily_Confirmations_{datetime.now().strftime('%Y%m%d')}.xlsx"
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response
    # =========================================================

    context = {
        'confirmation_records': confirmation_data,
        'filter_start_date': filter_start_date_str,
        'filter_end_date': filter_end_date_str,
    }
    
    return render(request, 'unity_internal_app/confirmations.html', context)


# --- Admin Billing View (Line-by-Line Display) ---

@login_required
def admin_billing_view(request):
    """
    Displays a raw, line-by-line list of bills ready for Admin Billing confirmation.
    Calculates a 0.3% Admin Fee per bill line based on monthly salary.
    
    UPDATED: 
    1. Only shows reconciled bills (is_reconciled=True).
    2. Strictly excludes bills with 0 members or R0.00 schedule amount.
    3. Updated fee calculation to 0.003 (0.3%).
    """
    from decimal import Decimal
    from datetime import datetime

    filter_start_date = request.GET.get('start_date')
    filter_end_date = request.GET.get('end_date')

    # Base Query: Order by CC Dates Month, then by Company Code
    bills_queryset = UnityBill.objects.all().order_by('-A_CCDatesMonth', 'C_Company_Code')
    
    # --- UPDATED FILTERS ---
    # 1. Must be Reconciled
    # 2. Exclude bills with 0 members (prevents N/A rows)
    # 3. Exclude bills with 0.00 schedule (prevents zero-fee rows)
    bills_queryset = bills_queryset.filter(
        is_reconciled=True
    ).exclude(
        E_Active_Members=0
    ).exclude(
        H_Schedule_Amount=0
    )

    if filter_start_date:
        try:
            start_dt = datetime.strptime(filter_start_date, '%Y-%m-%d').date()
            bills_queryset = bills_queryset.filter(A_CCDatesMonth__gte=start_dt)
        except ValueError:
            pass

    if filter_end_date:
        try:
            end_dt = datetime.strptime(filter_end_date, '%Y-%m-%d').date()
            bills_queryset = bills_queryset.filter(A_CCDatesMonth__lte=end_dt)
        except ValueError:
            pass
            
    final_bill_data = []
    
    for bill in bills_queryset:
        # Since we excluded 0.00 above, we know schedule_amount will be a valid positive number
        schedule_amount = bill.H_Schedule_Amount or Decimal('0.00')
        active_members = bill.E_Active_Members or 0 
        
        # 🚀 NEW: Calculate 0.3% Admin Fee (0.003) 🚀
        admin_fee = schedule_amount * Decimal('0.003')
        
        # Find the FIRST settlement record for metadata (Posted Date/User)
        first_settlement = BillSettlement.objects.filter(
            unity_bill_source_id=bill.pk
        ).order_by('settlement_date').first()
        
        posted_date = first_settlement.settlement_date if first_settlement else None
        
        # Get the username of the person who finalized the recon
        posted_user = "N/A"
        if first_settlement and first_settlement.confirmed_by:
            posted_user = first_settlement.confirmed_by.username
        
        fiscal_period_key = bill.A_CCDatesMonth.strftime("%Y-%m") if bill.A_CCDatesMonth else "N/A"

        final_bill_data.append({
            'fiscal_period': fiscal_period_key,
            'company_code': bill.C_Company_Code or "N/A",
            'company_name': bill.D_Company_Name or "N/A",
            'active_members': active_members, 
            'total_schedule_amount': schedule_amount,
            'total_admin_fee': admin_fee,
            'posted_date': posted_date,
            'posted_user': posted_user, 
        })

    context = {
        'bill_records': final_bill_data,
        'filter_start_date': filter_start_date,
        'filter_end_date': filter_end_date,
    }
    
    return render(request, 'unity_internal_app/admin_billing.html', context)

# ==============================================================================
# [UPDATED VIEWS] ADD THESE BELOW YOUR unity_information FUNCTION
# ==============================================================================

# In views.py

@login_required
def save_claim(request, company_code):
    if request.method == 'POST':
        claim_id = request.POST.get('claim_id')
        
        if claim_id:
            claim_instance = get_object_or_404(UnityClaim, pk=claim_id)
            form = UnityClaimForm(request.POST, instance=claim_instance)
        else:
            form = UnityClaimForm(request.POST)

        if form.is_valid():
            saved_claim = form.save(commit=False)

            # --- 1. CAPTURE NEW FIELDS (POTS & PRESERVATION) ---
            saved_claim.vested_pot_available = request.POST.get('vested_pot_available') == 'on'
            saved_claim.savings_pot_available = request.POST.get('savings_pot_available') == 'on'
            
            v_date = request.POST.get('vested_pot_paid_date')
            saved_claim.vested_pot_paid_date = v_date if v_date else None
            
            s_date = request.POST.get('savings_pot_paid_date')
            saved_claim.savings_pot_paid_date = s_date if s_date else None
            
            p_date = request.POST.get('infund_cert_date')
            saved_claim.infund_preservation_cert_received_date = p_date if p_date else None

            # --- 2. CAPTURE MIP & AMOUNT ---
            saved_claim.mip_number = request.POST.get('mip_number')
            
            amount_val = request.POST.get('claim_amount')
            if amount_val and amount_val.strip():
                try:
                    saved_claim.claim_amount = float(amount_val)
                except ValueError:
                    saved_claim.claim_amount = None
            else:
                saved_claim.claim_amount = None

            # --- 3. LINKED EMAIL LOGIC ---
            outlook_string_id = request.POST.get('linked_email_id')
            if outlook_string_id and outlook_string_id.strip():
                try:
                    email_obj = EmailDelegation.objects.get(email_id=outlook_string_id)
                    saved_claim.linked_email_id = email_obj.id
                    
                    UnityClaimNote.objects.create(
                        claim=saved_claim,
                        note_selection="SUBMITTED VIA E-MAIL",
                        note_description=f"System: Linked to Delegated Email Received at {email_obj.received_at}",
                        created_by=request.user
                    )
                except EmailDelegation.DoesNotExist:
                    saved_claim.linked_email_id = None

            saved_claim.save()

            # --- 4. Handle Manual Notes ---
            note_selection = request.POST.get('note_selection')
            note_description = request.POST.get('note_description')

            if note_selection or (note_description and note_description.strip()):
                UnityClaimNote.objects.create(
                    claim=saved_claim,
                    note_selection=note_selection,
                    note_description=note_description,
                    created_by=request.user
                )
                messages.success(request, "Claim saved and Notes updated.")
            else:
                messages.success(request, "Claim saved successfully.")
        else:
            messages.error(request, f"Error saving claim: {form.errors}")
            
    return redirect(f"{reverse('unity_information', kwargs={'company_code': company_code})}#company-claims")


@login_required
def global_claims_view(request):
    """
    Dashboard for all claims EXCEPT Two Pot.
    Integrated: Email Pre-loading for instant preview (No AJAX required).
    """
    query = request.GET.get('q')
    base_claims = UnityClaim.objects.exclude(claim_type='Two Pot')

    if query:
        claims = base_claims.filter(
            Q(id_number__icontains=query) | 
            Q(member_surname__icontains=query) | 
            Q(company_code__icontains=query)
        ).order_by('-claim_created_date')
    else:
        # Note: If using pagination later, apply it here. 
        # For now, we fetch the last 50 as per your original logic.
        claims = base_claims.order_by('-claim_created_date')[:50] 

    # --- 1. PRE-FETCH EMAIL CONTENT FOR TABLE ICONS ---
    # Collect IDs for any claims that have a linked email
    delegation_pks = [c.linked_email_id for c in claims if c.linked_email_id]
    
    if delegation_pks:
        # Map Delegation Primary Key -> Outlook String Email ID
        # Convert list to set to remove duplicates if multiple claims link to the same email
        delegations_map = EmailDelegation.objects.in_bulk(list(set(delegation_pks)))
        outlook_string_ids = [d.email_id for d in delegations_map.values()]
        
        # Map Outlook String Email ID -> Full Body/Subject Content
        inbox_map = OutlookInbox.objects.in_bulk(outlook_string_ids)

        for claim in claims:
            if claim.linked_email_id:
                try:
                    # Match the ID from the database to the pre-fetched map
                    del_obj = delegations_map.get(int(claim.linked_email_id))
                    if del_obj:
                        inbox_item = inbox_map.get(del_obj.email_id)
                        if inbox_item:
                            # Attach these temporarily to the object for the template <template>
                            claim.email_preview_subject = inbox_item.subject
                            claim.email_preview_sender = inbox_item.sender_address
                            claim.email_preview_body = inbox_item.body_content
                            claim.email_preview_date = inbox_item.received_at
                except (ValueError, TypeError):
                    continue

    all_companies = UnityMgListing.objects.values('a_company_code', 'b_company_name', 'c_agent')

    # --- 2. FETCH DELEGATIONS FOR MODAL DROPDOWN (Compose/Attach Logic) ---
    my_delegated_emails = EmailDelegation.objects.filter(
        assigned_user=request.user, 
        status='DEL'
    ).order_by('-received_at')

    # Attach basic info for dropdown display labels
    dropdown_email_ids = [d.email_id for d in my_delegated_emails]
    dropdown_inbox_items = OutlookInbox.objects.in_bulk(dropdown_email_ids)

    for delegation in my_delegated_emails:
        item = dropdown_inbox_items.get(delegation.email_id)
        if item:
            delegation.subject = item.subject
            delegation.sender = item.sender_address
        else:
            delegation.subject = "(Subject Unavailable)"
            delegation.sender = "Unknown"

    context = {
        'claims': claims,
        'all_companies': all_companies,
        'my_delegated_emails': my_delegated_emails,
        'is_two_pot_view': False
    }
    return render(request, 'unity_internal_app/global_claims.html', context)

@login_required
def global_two_pot_view(request):
    """
    Dedicated Dashboard for ONLY Two Pot claims with Date Range & Pagination.
    Integrated: Email Pre-loading for instant preview (No AJAX required).
    """
    query = request.GET.get('q')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    base_claims = UnityClaim.objects.filter(claim_type='Two Pot').order_by('-claim_created_date')

    # --- Filtering Logic ---
    if query:
        base_claims = base_claims.filter(
            Q(id_number__icontains=query) | 
            Q(member_surname__icontains=query) | 
            Q(company_code__icontains=query) |
            Q(mip_number__icontains=query)
        )

    if start_date and end_date:
        try:
            s_date = parse_date(start_date)
            e_date = parse_date(end_date)
            if s_date and e_date:
                base_claims = base_claims.filter(claim_created_date__range=[s_date, e_date])
        except ValueError:
            pass

    # --- Pagination ---
    paginator = Paginator(base_claims, 12) 
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # --- 1. PRE-FETCH EMAIL CONTENT FOR TABLE ICONS (Instant Preview Logic) ---
    # We collect all delegation IDs from the current page of claims to minimize DB hits
    delegation_pks = [c.linked_email_id for c in page_obj if c.linked_email_id]
    
    if delegation_pks:
        # Map Delegation Primary Key -> Outlook String Email ID
        delegations_map = EmailDelegation.objects.in_bulk(delegation_pks)
        outlook_string_ids = [d.email_id for d in delegations_map.values()]
        
        # Map Outlook String Email ID -> Full Body/Subject Content
        inbox_map = OutlookInbox.objects.in_bulk(outlook_string_ids)

        for claim in page_obj:
            if claim.linked_email_id:
                # Use int conversion to match in_bulk dictionary keys
                del_obj = delegations_map.get(int(claim.linked_email_id))
                if del_obj:
                    inbox_item = inbox_map.get(del_obj.email_id)
                    if inbox_item:
                        # Attach attributes directly to the claim object for the template <template>
                        claim.email_preview_subject = inbox_item.subject
                        claim.email_preview_sender = inbox_item.sender_address
                        claim.email_preview_body = inbox_item.body_content
                        claim.email_preview_date = inbox_item.received_at

    all_companies = UnityMgListing.objects.values('a_company_code', 'b_company_name', 'c_agent')

    # --- 2. FETCH DELEGATIONS FOR MODAL DROPDOWN (Compose/Attach Logic) ---
    my_delegated_emails = EmailDelegation.objects.filter(
        assigned_user=request.user, 
        status='DEL'
    ).order_by('-received_at')

    # Attach basic info for dropdown display labels
    dropdown_email_ids = [d.email_id for d in my_delegated_emails]
    dropdown_inbox_items = OutlookInbox.objects.in_bulk(dropdown_email_ids)

    for delegation in my_delegated_emails:
        item = dropdown_inbox_items.get(delegation.email_id)
        if item:
            delegation.subject = item.subject
            delegation.sender = item.sender_address
        else:
            delegation.subject = "(Subject Unavailable)"
            delegation.sender = "Unknown"

    context = {
        'page_obj': page_obj, 
        'all_companies': all_companies,
        'my_delegated_emails': my_delegated_emails,
        'is_two_pot_view': True,
        'search_query': query, 
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'unity_internal_app/global_two_pot.html', context)


@transaction.atomic
@login_required
def save_global_claim(request):
    if request.method == 'POST':
        # Determine where to redirect based on the claim type
        claim_type_input = request.POST.get('claim_type')
        redirect_url = 'global_two_pot' if claim_type_input == 'Two Pot' else 'global_claims'
        
        claim_id = request.POST.get('claim_id')
        
        # 1. Capture Old State to detect changes for logging
        old_linked_email_id = None
        if claim_id:
            claim_instance = get_object_or_404(UnityClaim, pk=claim_id)
            old_linked_email_id = claim_instance.linked_email_id
            form = UnityClaimForm(request.POST, request.FILES, instance=claim_instance)
        else:
            form = UnityClaimForm(request.POST, request.FILES)

        if form.is_valid():
            saved_claim = form.save(commit=False)
            
            # --- Two Pot Logic: Explicitly handle specific fields ---
            if claim_type_input == 'Two Pot':
                saved_claim.claim_type = 'Two Pot'
                saved_claim.mip_number = request.POST.get('mip_number')
                
                # Handle decimal/float for claim_amount safely
                amount = request.POST.get('claim_amount')
                if amount and amount.strip():
                    try:
                        saved_claim.claim_amount = float(amount)
                    except ValueError:
                        saved_claim.claim_amount = 0.00
                else:
                    saved_claim.claim_amount = 0.00

            # --- NEW Logic: Pot Availability and Certificates ---
            # Checkboxes return 'on' if checked, else None
            saved_claim.vested_pot_available = request.POST.get('vested_pot_available') == 'on'
            saved_claim.vested_pot_paid_date = request.POST.get('vested_pot_paid_date') or None

            saved_claim.savings_pot_available = request.POST.get('savings_pot_available') == 'on'
            saved_claim.savings_pot_paid_date = request.POST.get('savings_pot_paid_date') or None

            # In-Fund Preservation
            saved_claim.infund_preservation_cert_received_date = request.POST.get('infund_cert_date') or None

            # --- Explicitly Handle Linked Email ID (ID reference) ---
            new_linked_email_id = request.POST.get('linked_email_id')
            if new_linked_email_id and new_linked_email_id.strip():
                saved_claim.linked_email_id = new_linked_email_id

            if 'claim_attachment' in request.FILES:
                saved_claim.claim_attachment = request.FILES['claim_attachment']

            saved_claim.save()

            # ---------------------------------------------------------------
            # 2. LOG EMAIL LINK: Create a note if the link has changed
            # ---------------------------------------------------------------
            str_old = str(old_linked_email_id) if old_linked_email_id else ""
            str_new = str(new_linked_email_id) if new_linked_email_id else ""

            if str_new and str_new != str_old:
                UnityClaimNote.objects.create(
                    claim=saved_claim,
                    note_selection="SUBMITTED VIA E-MAIL",
                    note_description=f"System: Attached Delegated Email ID #{str_new}",
                    created_by=request.user
                )

            # ---------------------------------------------------------------
            # 3. LOGIC: HANDLE "COMPOSE & SEND" EMAIL
            # ---------------------------------------------------------------
            email_action = request.POST.get('email_submission_action')
            if email_action == 'send_email_and_log':
                recipient = request.POST.get('member_recipient_email')
                subject = request.POST.get('member_email_subject_reply')
                email_body_html = request.POST.get('email_body_html_content')

                if recipient and email_body_html:
                    response = OutlookGraphService.send_outlook_email(
                        settings.OUTLOOK_EMAIL_ADDRESS, recipient, subject, email_body_html, 'HTML'
                    )
                    
                    if response.get('success'):
                        UnityClaimNote.objects.create(
                            claim=saved_claim,
                            note_selection="SUBMITTED VIA E-MAIL",
                            note_description=f"EMAIL SENT SUCCESSFULLY\nTo: {recipient}\nSubject: {subject}",
                            created_by=request.user
                        )
                        messages.success(request, f"Email sent to {recipient} and claim saved.")
                    else:
                        messages.warning(request, f"Claim saved, but Email failed: {response.get('error')}")

            # ---------------------------------------------------------------
            # 4. LOGIC: MANUAL TEXT NOTE / STATUS HELPER NOTE
            # ---------------------------------------------------------------
            note_selection = request.POST.get('note_selection') or "GENERAL NOTE"
            note_description = request.POST.get('note_description')

            if note_description and note_description.strip():
                UnityClaimNote.objects.create(
                    claim=saved_claim,
                    note_selection=note_selection,
                    note_description=note_description,
                    created_by=request.user
                )
            
            if not messages.get_messages(request):
                messages.success(request, "Claim saved successfully.")
                
            return redirect(redirect_url)
            
        else:
            messages.error(request, f"Error saving claim: {form.errors}")
            return redirect(redirect_url)
            
    return redirect('global_claims')
# --------------------------------------------------------------------- #
# OUTLOOK DELEGATOR VIEWS (Inbox & Assignment)
# --------------------------------------------------------------------- #

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse # Import HttpResponse for the content view
from dateutil import parser # Ensure parser is imported
from django.contrib.auth import get_user_model # Use get_user_model for clarity

# Services and Models (Assuming these imports are correct based on our prior conversation)
from .models import EmailDelegation
from .services.delegation_service import (
    get_or_create_delegation_status, delegate_email_task, 
    add_delegation_note, get_delegated_emails_for_user, 
    log_delegation_transaction
)
# Correct import: only import the class, and use the class name to call methods
from .services.outlook_graph_service import OutlookGraphService 

User = get_user_model() # Alias for the User model

# Assuming there are other required imports here (e.g., from unity_internal_app.models import ...)


@login_required
def outlook_dashboard_view(request):
    """
    Displays the Inbox. 
    Shows ONLY emails that are NEW. 
    Explicitly excludes 'DEL' (Delegated) and 'DLT' (Deleted/Recycle Bin).
    UPDATED: Pulls received_at from local OutlookInbox model.
    """
    if request.user.username.lower() != 'omega' and not request.user.is_superuser:
        messages.error(request, "Access restricted.")
        return redirect('outlook_delegated_box')

    target_email = request.GET.get('email', settings.OUTLOOK_EMAIL_ADDRESS)
    context = {'target_email': target_email, 'messages': []}
    
    inbox_data = OutlookGraphService.fetch_inbox_messages(target_email, top_count=50) 
    
    if 'error' not in inbox_data:
        all_emails = inbox_data.get('value', [])
        email_ids = [e['id'] for e in all_emails]
        
        # Fetch local inbox records to get the stored received_at date
        # Use in_bulk for efficient ID-based mapping
        local_inbox_map = OutlookInbox.objects.filter(email_id__in=email_ids).in_bulk(field_name='email_id')

        # LOGIC: Exclude anything that isn't NEW
        delegated_or_recycled_ids = EmailDelegation.objects.filter(
            email_id__in=email_ids
        ).exclude(status='NEW').values_list('email_id', flat=True)
        
        filtered_emails = []
        for email in all_emails:
            email_id = email['id']
            if email_id in delegated_or_recycled_ids:
                continue
                
            received_date_str = email.get('receivedDateTime') 
            
            # Ensure a NEW record exists in Delegation
            delegation, created = EmailDelegation.objects.get_or_create(
                email_id=email_id,
                defaults={'received_at': received_date_str, 'status': 'NEW'}
            )
            
            # ATTACH LOCAL TIMESTAMP: 
            # If the item exists in OutlookInbox, use that date. Otherwise, fallback to Graph date.
            local_record = local_inbox_map.get(email_id)
            if local_record:
                email['internal_received_at'] = local_record.received_at
            else:
                email['internal_received_at'] = received_date_str

            email['delegation_status'] = delegation.get_status_display()
            email['delegation_id'] = delegation.pk 
            filtered_emails.append(email)
            
        context['messages'] = filtered_emails
    else:
        context['error'] = inbox_data['error']

    return render(request, 'unity_internal_app/outlook_dashboard.html', context)


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
        # 🛑 FIX 1: Define body_html (using 'body' content, assuming HTML) 🛑
        body_html = request.POST.get('body') 
        # 🛑 FIX 2: Define sender (the delegated mailbox) 🛑
        sender = target_email 

        # Simple validation
        if not all([recipient, subject, body_html]):
            messages.error(request, "All fields are required.")
            return render(request, 'unity_internal_app/send_email_form.html', {'target_email': target_email})
        
        # Call the service function, passing the target_email as the sender mailbox
        # Line 3212 (Approximate):
        response = OutlookGraphService.send_outlook_email(sender, recipient, subject, body_html, 'HTML')
        
        # 🛑 FIX 3: Change 'result' to 'response' (Line 3214 Approx.) 🛑
        if response.get('success'): 
            messages.success(request, f"Email sent successfully from {target_email} to {recipient}.")
            # Redirect back to the dashboard, preserving the target email
            return redirect(f"{reverse('outlook_dashboard')}?email={target_email}")
        else:
            error_message = f"Email failed to send from {target_email}. {response.get('error', 'Unknown API Error')}"
            
            # Extract details if they exist in the nested error structure
            details = response.get('details', {})
            if isinstance(details, dict) and 'error' in details and 'message' in details['error']:
                error_message += f" Details: {details['error']['message']}"
            
            messages.error(request, error_message)
            # Render the form again with the failure message
            return render(request, 'unity_internal_app/send_email_form.html', {
                'recipient': recipient,
                'subject': subject,
                'body': body_html, # Pass the correct variable back to the form
                'target_email': target_email
            })

    # Render the empty form on GET request
    return render(request, 'unity_internal_app/send_email_form.html', {'target_email': target_email})


# --------------------------------------------------------------------- #
# OUTLOOK DELEGATED VIEWS (Assigned User Workflow)
# --------------------------------------------------------------------- #

@login_required
def outlook_delegated_box(request):
    """
    Displays the list of tasks specifically assigned to the current user.
    Strictly filters for Status='DEL' to distinguish from 'DLT' (Recycle Bin).
    """
    # 1. Fetch only ACTIVE delegations for this user
    # Note: If your helper 'get_delegated_emails_for_user' doesn't filter by status, 
    # use the direct QuerySet below:
    delegations = EmailDelegation.objects.filter(
        assigned_user=request.user, 
        status='DEL'
    ).order_by('-received_at')

    tasks = []
    target_email = settings.OUTLOOK_EMAIL_ADDRESS 

    for delegation in delegations:
        # Fetch subject/sender details from Graph for display
        endpoint = f"messages/{delegation.email_id}?$select=subject,from,receivedDateTime"
        
        try:
            # Execute GET request to Graph API
            response = OutlookGraphService._make_graph_request(
                endpoint, 
                target_email, 
                method='GET'
            )
            
            # Check for API errors or empty response
            if response and 'error' not in response:
                tasks.append({
                    'delegation_id': delegation.pk,
                    'status': delegation.get_status_display(), # Shows "Delegated" labels
                    'subject': response.get('subject', '(No Subject)'),
                    'from': response.get('from', {}).get('emailAddress', {}).get('name', 'Unknown Sender'),
                    'received': response.get('receivedDateTime'),
                    'company_code': delegation.company_code, # Added for better UI context
                })
            else:
                # Optional: log specific Graph API failures for individual items
                pass

        except Exception as e:
            # Fallback for UI if Graph API is unreachable for a specific message
            tasks.append({
                'delegation_id': delegation.pk,
                'status': delegation.get_status_display(),
                'subject': f"[Graph Error: {delegation.email_id[:8]}...]",
                'from': "N/A",
                'received': delegation.received_at
            })

    context = {
        'tasks': tasks,
        'task_count': len(tasks)
    }
    return render(request, 'unity_internal_app/outlook_delegated_box.html', context)


@login_required
def outlook_delegated_action(request, delegation_id):
    """
    Handles Notes, Replies, Metadata Updates, RESTORATION, and COMPLETION.
    UPDATED: Fetches attachment metadata and raw bytes for image previews.
    """
    delegation = get_object_or_404(EmailDelegation, pk=delegation_id)
    
    # --- ROLE-BASED ACCESS CONTROL ---
    is_manager = request.user.username.lower() == 'omega' or request.user.is_superuser
    
    if not is_manager and delegation.assigned_user != request.user:
        messages.error(request, "Access restricted. You are not assigned to this task.")
        return redirect('outlook_delegated_box')

    target_email = settings.OUTLOOK_EMAIL_ADDRESS 

    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        # --- 1. HANDLE RESTORE ---
        if action_type == 'restore_to_inbox':
            delegation.work_related = True
            delegation.status = 'NEW'
            delegation.assigned_user = None 
            delegation.save()

            add_delegation_note(
                delegation_id, 
                request.user, 
                "ACTION: Restored task from Recycle Bin to Main Inbox queue."
            )
            messages.success(request, "Email successfully restored to the Live Inbox.")
            return redirect('outlook_recycle_bin')

        # --- 2. HANDLE COMPLETE ---
        elif action_type == 'mark_complete':
            delegation.status = 'COM'  # Completed / Actioned
            delegation.save()

            add_delegation_note(
                delegation_id, 
                request.user, 
                "ACTION: Task marked as COMPLETED. Removed from active queue."
            )
            messages.success(request, "Task successfully marked as Completed.")
            return redirect('outlook_delegated_box')

        # --- 3. HANDLE METADATA UPDATES ---
        elif action_type == 'update_metadata':
            delegation.company_code = request.POST.get('company_code')
            delegation.email_category = request.POST.get('email_category')
            delegation.status = request.POST.get('status')
            delegation.save()

            add_delegation_note(
                delegation_id, 
                request.user, 
                f"SYSTEM: Metadata Updated. Status: [{delegation.status}], Category: [{delegation.email_category}]"
            )
            messages.success(request, "Task metadata updated successfully.")
            return redirect('outlook_delegated_action', delegation_id=delegation_id)

        # --- 4. HANDLE NOTE SUBMISSION ---
        elif 'note_content' in request.POST:
            note_content = request.POST.get('note_content')
            success, message = add_delegation_note(delegation_id, request.user, note_content)
            if success: 
                messages.success(request, "Internal note saved.")
            else:
                messages.error(request, message)
            return redirect('outlook_delegated_action', delegation_id=delegation_id)
        
        # --- 5. HANDLE REPLY/SEND EMAIL ---
        elif 'reply_recipient' in request.POST:
            recipient = request.POST.get('reply_recipient')
            raw_subject = request.POST.get('reply_subject')
            subject = raw_subject if raw_subject else f"Reply: {delegation.email_category or 'Task Action'}"
            body_html = request.POST.get('reply_body')
            action_destination = request.POST.get('action_notes', 'EMAIL_REPLY')
            
            log_type = request.POST.get('email_log_type', 'DIRECT') 

            response = OutlookGraphService.send_outlook_email(target_email, recipient, subject, body_html)
            
            if response.get('success'):
                final_action_type = 'REPLIED' if log_type == 'REPLY' else action_destination
                
                log_delegation_transaction(
                    delegation_id, 
                    request.user, 
                    subject, 
                    recipient, 
                    action_type=final_action_type 
                )
                
                messages.success(request, f"Reply sent successfully and logged as {final_action_type}.")
            else:
                messages.error(request, f"Failed to send email: {response.get('error')}")
                
            return redirect('outlook_delegated_action', delegation_id=delegation_id)

    # --- GET DATA ---
    endpoint = f"messages/{delegation.email_id}"
    email_data = OutlookGraphService._make_graph_request(endpoint, target_email, method='GET')
    
    # Fetch Attachment Metadata
    attachments = OutlookGraphService.fetch_attachments(target_email, delegation.email_id)
    
    # 🚀 NEW: Loop through attachments to fetch contentBytes for image previews
    for att in attachments:
        content_type = att.get('contentType', '').lower()
        # If it's an image, we fetch the full raw data to get 'contentBytes' for <img> tags
        if 'image' in content_type:
            raw_att = OutlookGraphService.get_attachment_raw(target_email, delegation.email_id, att['id'])
            if 'contentBytes' in raw_att:
                att['contentBytes'] = raw_att['contentBytes']
    
    if 'error' in email_data:
        messages.warning(request, "Could not fetch live email content. Showing local snippet instead.")
        email_display = {'subject': delegation.email_id, 'body': {'content': 'Live content unavailable.'}}
    else:
        email_display = email_data

    context = {
        'delegation': delegation,
        'email': email_display,
        'attachments': attachments,  # Now includes contentBytes for images
        'notes': delegation.notes.all().order_by('-created_at'),
        'target_email': target_email,
        'is_manager': is_manager,
    }
    return render(request, 'unity_internal_app/outlook_delegated_action.html', context)

@login_required
def outlook_delegate_to(request, email_id):
    """
    Handles the detailed delegation form for classification before assignment.
    UPDATED: Fetches attachment metadata and raw bytes for image previews.
    """
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    available_users = User.objects.filter(is_active=True).exclude(pk=request.user.pk)
    
    if request.method == 'POST':
        work_related_input = request.POST.get('work_related')
        assignee_pk = request.POST.get('agent_name')
        
        data_for_delegation = {
            'company_code': request.POST.get('company_code'),
            'email_category': request.POST.get('email_category'),
            'work_related': True if work_related_input == 'Yes' else False,
            'comm_type': request.POST.get('comm_type') or 'Email',
        }

        if work_related_input == 'No':
            from .models import EmailDelegation
            EmailDelegation.objects.update_or_create(
                email_id=email_id,
                defaults={
                    'work_related': False,
                    'status': 'DLT',  
                    'assigned_user': None,
                    'company_code': data_for_delegation['company_code'],
                    'email_category': data_for_delegation['email_category'],
                    'communication_type': data_for_delegation['comm_type'],
                }
            )
            messages.error(request, "Email moved to Recycle Bin (Status: DLT).")
            return redirect('outlook_dashboard')

        else:
            if not assignee_pk or assignee_pk in ['', '__Select Agent__']:
                messages.error(request, "Please select an agent for delegation.")
            else:
                success, message = delegate_email_task(
                    email_id, 
                    assignee_pk, 
                    request.user, 
                    classification_data=data_for_delegation
                )
                
                if success:
                    assignee = User.objects.get(pk=assignee_pk)
                    reply_endpoint = f"messages/{email_id}/createReply"
                    reply_payload = {
                        "comment": f"Dear Sender,\n\nThis request has been successfully received and delegated to our agent: {assignee.username}.\n\nPlease use Reference: {data_for_delegation['company_code'] or 'N/A'} for future queries.\n\nRegards,\nMIP Support Team"
                    }
                    
                    try:
                        draft_response = OutlookGraphService._make_graph_request(
                            reply_endpoint, target_email, method='POST', data=reply_payload
                        )
                        if 'id' in draft_response:
                            send_endpoint = f"messages/{draft_response['id']}/send"
                            OutlookGraphService._make_graph_request(send_endpoint, target_email, method='POST')
                            messages.success(request, f"Task delegated and confirmation email sent!")
                    except Exception as e:
                        messages.warning(request, f"Delegation saved, but reply failed: {str(e)}")

                    return redirect('outlook_dashboard')
                else:
                    messages.error(request, message)

    # --- Fetch Data for GET Request ---
    endpoint = f"messages/{email_id}" 
    email_data = OutlookGraphService._make_graph_request(endpoint, target_email, method='GET') 

    if 'error' in email_data:
        messages.error(request, f"Error fetching email content: {email_data.get('error')}")
        return redirect('outlook_dashboard')

    # Fetch Attachments Metadata
    attachments_data = OutlookGraphService.fetch_attachments(target_email, email_id)
    
    # 🚀 NEW: Fetch content bytes for images to allow thumbnails in the delegation form
    for att in attachments_data:
        content_type = att.get('contentType', '').lower()
        if 'image' in content_type:
            raw_att = OutlookGraphService.get_attachment_raw(target_email, email_id, att['id'])
            if 'contentBytes' in raw_att:
                att['contentBytes'] = raw_att['contentBytes']
    
    raw_content = email_data.get('body', {}).get('content', '')
    received_date_str = email_data.get('receivedDateTime')
    
    get_or_create_delegation_status(email_id, received_date_str=received_date_str)
    
    context = {
        'email_id': email_id,
        'email_subject': email_data.get('subject', '(No Subject)'),
        'email_content': raw_content, 
        'attachments': attachments_data, 
        'available_users': available_users,
    }
    return render(request, 'unity_internal_app/outlook_delegate_to.html', context)

def outlook_email_content(request, email_id):
    """
    Fetches the raw HTML content of an email and returns it as a response 
    to be loaded by an iframe's 'src' attribute.
    """
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    endpoint = f"messages/{email_id}" 
    
    # 🛑 FIX 11: Define 'method' and 'email_data' for this GET request 🛑
    method = 'GET'
    email_data = None
    
    email_data = OutlookGraphService._make_graph_request(endpoint, target_email, method=method, data=email_data)

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

@login_required
def outlook_recycle_bin_view(request):
    """
    Displays all emails marked as DLT (Recycle Bin).
    Maps email_id to the actual subject stored in OutlookInbox for better readability.
    """
    # 1. Fetch delegations marked as DLT or not work-related
    recycled_tasks = EmailDelegation.objects.filter(status='DLT').order_by('-received_at')
    
    # 2. Extract email IDs to fetch subjects in bulk
    email_ids = [task.email_id for task in recycled_tasks]
    
    # 3. Create a map of {email_id: subject} from the OutlookInbox model
    inbox_details = OutlookInbox.objects.filter(email_id__in=email_ids).values('email_id', 'subject')
    subject_map = {item['email_id']: item['subject'] for item in inbox_details}
    
    # 4. Attach the subject to each task object
    for task in recycled_tasks:
        # Fallback to truncated ID if subject isn't found in local cache
        task.subject_display = subject_map.get(task.email_id, f"ID: {task.email_id[:15]}...")

    return render(request, 'unity_internal_app/recycle_bin.html', {
        'recycled_tasks': recycled_tasks
    })

@login_required
def outlook_restore_email(request, email_id):
    """Restores a task by setting work_related back to True."""
    task = get_object_or_404(EmailDelegation, email_id=email_id)
    task.work_related = True
    task.status = 'NEW'  
    task.save()
    
    DelegationNote.objects.create(
        delegation=task,
        user=request.user,
        content="Task restored from Recycle Bin."
    )
    
    messages.success(request, "Email restored to Live Inbox.")
    # FIX: Match the name in urls.py
    return redirect('outlook_recycle_bin')

@login_required
def outlook_delete_permanent(request):
    """
    Hides items from the Recycle Bin by moving them to ARC status.
    This avoids IntegrityErrors with foreign key notes while removing them from the UI.
    """
    if request.method == 'POST':
        email_ids = request.POST.getlist('email_ids')
        
        if email_ids:
            # Move from 'DLT' (Recycle Bin) to 'ARC' (Hidden/Archived)
            # This satisfies the DB constraint because the row still exists, 
            # but it will no longer show up in the filter(status='DLT') query.
            EmailDelegation.objects.filter(email_id__in=email_ids).update(status='ARC')
            
            messages.success(request, f"Successfully removed {len(email_ids)} items from the Recycle Bin.")
        else:
            messages.warning(request, "No items were selected for removal.")
            
        return redirect('outlook_recycle_bin')
    
@login_required
def view_email_thread(request, email_id):
    """
    Displays the historical timeline and the original email content with 
    attachment previews/downloads.
    """
    # 1. Fetch the original delegated email item from local DB
    task = get_object_or_404(EmailDelegation, email_id=email_id)
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    
    # 2. Fetch Live Content from Graph API
    # This ensures the history view shows the full original HTML and current attachments
    endpoint = f"messages/{email_id}"
    email_data = OutlookGraphService._make_graph_request(endpoint, target_email, method='GET')
    
    attachments = []
    if 'error' not in email_data:
        # Fetch Attachment Metadata
        attachments = OutlookGraphService.fetch_attachments(target_email, email_id)
        
        # Fetch bytes for images to show thumbnails in the history timeline
        for att in attachments:
            if 'image' in att.get('contentType', '').lower():
                raw_att = OutlookGraphService.get_attachment_raw(target_email, email_id, att['id'])
                att['contentBytes'] = raw_att.get('contentBytes')
        
        # Use live body content if available, otherwise fallback to task attribute
        email_body = email_data.get('body', {}).get('content', '')
    else:
        # Fallback to local task data if Graph API call fails
        email_body = getattr(task, 'body_content', "Live content unavailable.")

    # 3. Fetch Transaction Log (Timeline)
    actions = DelegationTransactionLog.objects.filter(
        delegation=task
    ).select_related('user').order_by('-timestamp')

    context = {
        'task': task,
        'email': email_data, # Metadata like Sender/Subject
        'email_body': email_body,
        'attachments': attachments,
        'actions': actions,
        'inbox_item': task, 
    }
    
    return render(request, 'unity_internal_app/view_email_thread.html', context)

@login_required
def email_list_view(request):
    """
    MASTER ARCHIVE: Displays all delegated tasks and transaction logs.
    Fix: Using delegation_id for transaction log lookup.
    """
    filter_type = request.GET.get('type', 'all')
    
    # 1. Fetch all Delegation Tasks (excluding Recycle Bin)
    delegations_qs = EmailDelegation.objects.exclude(status__in=['DLT', 'ARC']).order_by('-received_at')
    
    # FIX: delegation_id is the correct field in DelegationTransactionLog
    # We get a set of IDs for delegations that have at least one log entry
    all_log_delegation_ids = DelegationTransactionLog.objects.values_list('delegation_id', flat=True)
    emails_with_replies = set(all_log_delegation_ids) 

    # Fetch inbox map for details
    inbox_map = {obj.email_id: obj for obj in OutlookInbox.objects.all()}
    
    filtered_delegations = []
    for d in delegations_qs:
        # CHECK LOGIC: Does this specific delegation instance have any replies?
        has_reply = d.id in emails_with_replies
        
        # APPLY RULE: (NEW) OR (COM) OR (DEL with a reply)
        should_show = (d.status == 'NEW') or (d.status == 'COM') or (d.status == 'DEL' and has_reply)
        
        if should_show:
            inbox_detail = inbox_map.get(d.email_id)
            if inbox_detail:
                d.subject = inbox_detail.subject
                d.sender_address = inbox_detail.sender_address
            else:
                d.subject = f"[Details Missing - ID: {d.email_id[:10]}]"
                d.sender_address = "Unknown"
            
            filtered_delegations.append(d)

    # 2. Fetch Transaction Logs as independent items for the combined archive
    transactions = list(DelegationTransactionLog.objects.all().order_by('-timestamp'))

    # Category filtering
    if filter_type == 'new':
        items = [d for d in filtered_delegations if d.status == 'NEW']
    elif filter_type == 'delegated':
        items = [d for d in filtered_delegations if d.status == 'DEL']
    elif filter_type == 'reply':
        items = transactions
    else:
        # Combined list sorted by date
        items = sorted(
            filtered_delegations + transactions, 
            key=lambda x: x.received_at if hasattr(x, 'received_at') and x.received_at else (x.timestamp if hasattr(x, 'timestamp') else timezone.now()), 
            reverse=True
        )

    # Pagination
    paginator = Paginator(items, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'unity_internal_app/email_list.html', {
        'page_obj': page_obj,
        'current_filter': filter_type
    })
    
@login_required
def export_two_pot_excel(request):
    """
    Exports Two-Pot claims to Excel.
    UPDATED: Branch now maps to Member Group Name (MGC Name).
    """
    query = request.GET.get('q')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    claims_queryset = UnityClaim.objects.filter(claim_type='Two Pot').order_by('-claim_created_date')

    if query:
        claims_queryset = claims_queryset.filter(
            Q(id_number__icontains=query) | 
            Q(member_surname__icontains=query) | 
            Q(company_code__icontains=query) |
            Q(mip_number__icontains=query)
        )

    if start_date and end_date:
        try:
            claims_queryset = claims_queryset.filter(claim_created_date__range=[start_date, end_date])
        except ValueError:
            pass

    # --- PRE-FETCH MEMBER GROUP NAMES FOR THE BRANCH COLUMN ---
    # Fetch distinct company codes from the queryset to minimize DB hits
    company_codes = claims_queryset.values_list('company_code', flat=True).distinct()
    mg_map = {
        item['a_company_code']: item['b_company_name'] 
        for item in UnityMgListing.objects.filter(a_company_code__in=company_codes).values('a_company_code', 'b_company_name')
    }

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Two Pot Extract"

    headers = [
        "DATE EXTRACT INFO / FORM FROM WEB - Savings Form Request",
        "Initials",
        "Surname",
        "Member number",
        "ID NUMBER",
        "Fund",
        "Branch", # Maps to Member Group Name
        "Query",
        "Claim",
        "Qualified",
        "Date submitted/ online",
        "Succesfull Loaded confirmation",
        "Amount Apply for",
        "Admin Fee R33 + 15% Vat",
        "Note"
    ]
    ws.append(headers)

    for claim in claims_queryset:
        initials = claim.member_name[:1] if claim.member_name else ""
        
        # Qualified Logic
        status_text = str(claim.claim_status).strip()
        if "Withdraw" in status_text: 
            qualified_logic = "No"
        else:
            qualified_logic = "Yes"
        
        latest_note_obj = claim.notes.last()
        note_content = latest_note_obj.note_description if latest_note_obj else ""

        # Fetch the Member Group Name using the company_code
        branch_name = mg_map.get(claim.company_code, "Unknown Group")

        row = [
            claim.claim_created_date,               # DATE EXTRACT
            initials,                               # Initials
            claim.member_surname,                   # Surname
            claim.mip_number,                       # Member number
            claim.id_number,                        # ID NUMBER
            claim.company_code,                     # Fund (MG)
            branch_name,                            # Branch (MGC Name) - UPDATED
            'Savings form request',                 # Query
            claim.claim_status,                     # Claim
            qualified_logic,                        # Qualified
            claim.date_submitted,                   # Date submitted
            qualified_logic,                        # Succesfull Loaded
            claim.claim_amount,                     # Amount Apply for
            37.95,                                  # Admin Fee
            note_content                            # Note
        ]
        ws.append(row)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Two_Pot_Export.xlsx"'
    wb.save(response)
    return response

@login_required
def export_global_claims_excel(request):
    """
    Exports Global Claims to Excel.
    UPDATED: Excludes Two-Pot, Branch = Member Group Name lookup.
    """
    query = request.GET.get('q')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    claim_type_filter = request.GET.get('claim_type')

    # FIX: Exclude Two Pot from the Global Export
    claims_queryset = UnityClaim.objects.exclude(claim_type='Two Pot').order_by('-claim_created_date')

    if query:
        claims_queryset = claims_queryset.filter(
            Q(id_number__icontains=query) | 
            Q(member_surname__icontains=query) | 
            Q(company_code__icontains=query) |
            Q(mip_number__icontains=query)
        )

    if start_date and end_date:
        try:
            claims_queryset = claims_queryset.filter(claim_created_date__range=[start_date, end_date])
        except ValueError:
            pass

    if claim_type_filter and claim_type_filter != "All":
        claims_queryset = claims_queryset.filter(claim_type=claim_type_filter)

    # Pre-fetch Company Names for the "Branch" requirement
    # This avoids doing a database query inside the loop for every single row
    company_codes = claims_queryset.values_list('company_code', flat=True).distinct()
    mg_map = {
        item['a_company_code']: item['b_company_name'] 
        for item in UnityMgListing.objects.filter(a_company_code__in=company_codes).values('a_company_code', 'b_company_name')
    }

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Global Claims Extract"

    headers = [
        "Company Code",
        "Branch", # Was Agent, now Branch (Member Group Name)
        "Agent",
        "ID Number",
        "Member Name",
        "Member Surname",
        "MIP Number",
        "Claim Type",
        "Exit Reason",
        "Claim Allocation",
        "Claim Status",
        "Payment Option",
        "Claim Created Date",
        "Last Contribution Date",
        "Date Submitted",
        "Date Paid",
        "Vested Pot available",
        "Vested Pot Paid",
        "Savings Pot available",
        "Savings Pot Paid",
        "Infund Preservation"
    ]
    ws.append(headers)

    for claim in claims_queryset:
        vested_avail = "Yes" if claim.vested_pot_available else ""
        savings_avail = "Yes" if claim.savings_pot_available else ""
        
        # Look up Member Group Name for the Branch column
        branch_name = mg_map.get(claim.company_code, "Unknown Group")

        row = [
            claim.company_code,
            branch_name,            # Branch = Member_Group_Name
            claim.agent,
            claim.id_number,
            claim.member_name,
            claim.member_surname,
            claim.mip_number,
            claim.claim_type,
            claim.exit_reason,
            claim.claim_allocation,
            claim.claim_status,
            claim.payment_option,
            claim.claim_created_date,
            claim.last_contribution_date,
            claim.date_submitted,
            claim.date_paid,
            vested_avail,
            claim.vested_pot_paid_date,
            savings_avail,
            claim.savings_pot_paid_date,
            claim.infund_preservation_cert_received_date
        ]
        ws.append(row)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Global_Claims_Export.xlsx"'
    wb.save(response)
    return response

@login_required
def manager_approval_dashboard(request):
    """
    Lists all Credit Notes waiting for Linking Approval.
    """
    pending_credits = CreditNote.objects.filter(credit_link_status='Pending').order_by('-processed_date')
    
    context = {
        'pending_credits': pending_credits
    }
    return render(request, 'unity_internal_app/manager_approval_dashboard.html', context)

@login_required
@transaction.atomic
def approve_credit_link(request, note_id):
    """
    Manager Approval Logic.
    UPDATED: Handles "Overs credit line" differently. 
    - If it's an 'Overs' line: It is approved to become a usable credit (Unlinked).
    - If it's a standard link request: It allocates money to a specific bill.
    """
    from decimal import Decimal
    from django.db.models import Sum
    from django.utils import timezone
    from django.contrib import messages
    from django.shortcuts import redirect, get_object_or_404
    from .models import CreditNote, BillSettlement

    note = get_object_or_404(CreditNote, id=note_id)
    ZERO_DECIMAL = Decimal('0.00')
    
    if note.credit_link_status != 'Pending':
        messages.error(request, "This credit is not pending approval.")
        return redirect('manager_approval_dashboard')

    # --- NEW LOGIC: HANDLE "OVERS CREDIT LINE" VERIFICATION ---
    # If the reason is 'Overs credit line', the manager is just verifying the 
    # bank overpayment is valid. It doesn't get applied to a bill immediately.
    if note.link_request_reason == "Overs credit line":
        note.credit_link_status = 'Unlinked' # Now available for future bill requests
        note.pending_linked_bill = None
        note.authorized_by = request.user.username
        note.authorized_at = timezone.now()
        note.save()
        
        messages.success(request, f"Overs credit line of R{note.schedule_amount} verified and released to Member Group {note.member_group_code}.")
        return redirect('manager_approval_dashboard')

    # --- EXISTING LOGIC: HANDLE BILL ALLOCATION REQUESTS ---
    target_bill = note.pending_linked_bill
    if not target_bill:
        # Fallback: if no bill and not an 'Overs', reset to Unlinked
        note.credit_link_status = 'Unlinked'
        note.save()
        messages.warning(request, "Request reset: No target bill was attached to this link request.")
        return redirect('manager_approval_dashboard')

    # 1. Calculate Cap to prevent over-settling the bill
    total_already_settled = BillSettlement.objects.filter(
        unity_bill_source_id=target_bill.pk
    ).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
    
    bill_remaining_debt = target_bill.H_Schedule_Amount - total_already_settled
    
    # Use the amount the agent requested
    current_temp_request = note.requested_amount or ZERO_DECIMAL
    final_allocation = min(current_temp_request, bill_remaining_debt)

    if final_allocation <= ZERO_DECIMAL:
        messages.warning(request, f"Bill #{target_bill.id} is already fully paid. Credit reset to Unlinked.")
        note.credit_link_status = 'Unlinked'
        note.pending_linked_bill = None
        note.requested_amount = ZERO_DECIMAL 
        note.save()
        return redirect('manager_approval_dashboard')

    # 2. Update Balances
    # Subtract from available balance
    note.schedule_amount -= final_allocation 
    # Store what was actually used
    note.requested_amount = final_allocation 

    if note.schedule_amount <= ZERO_DECIMAL:
        note.assigned_unity_bill = target_bill
        note.credit_link_status = 'Approved' # Fully consumed
    else:
        note.assigned_unity_bill = None
        note.credit_link_status = 'Unlinked' # Partial remains for future use

    note.pending_linked_bill = None
    note.authorized_by = request.user.username
    note.authorized_at = timezone.now()
    note.save()

    # 3. Create Audit Trail
    BillSettlement.objects.create(
        unity_bill_source=target_bill,
        settled_amount=final_allocation,
        settlement_date=timezone.now(),
        source_credit_note_id=note.id,
        reconned_bank_line=None
    )

    messages.success(request, f"Approved R{final_allocation} for Bill #{target_bill.id}.")
    return redirect('manager_approval_dashboard')

@login_required
@transaction.atomic
def reject_credit_link(request, note_id):
    from django.contrib import messages
    from django.shortcuts import redirect, get_object_or_404
    from .models import CreditNote

    note = get_object_or_404(CreditNote, id=note_id)
    
    if note.credit_link_status != 'Pending':
        messages.error(request, "This credit is not in a pending state.")
        return redirect('manager_approval_dashboard')

    # --- UPDATED LOGIC ---
    # If the manager rejects it, we move it back to 'Unlinked'
    # This allows the clerk to try the request again or fix a mistake.
    note.credit_link_status = 'Unlinked'
    note.pending_linked_bill = None
    note.requested_amount = 0  
    
    # Track who rejected it for the audit trail
    note.review_note = f"Rejected by {request.user.username} on {timezone.now().date()}"
    note.save()

    messages.warning(request, f"Credit ID {note_id} was rejected and returned to the unlinked pool.")
    return redirect('manager_approval_dashboard')

@login_required
def global_bank_view(request):
    query = request.GET.get('q')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    base_queryset = ReconnedBank.objects.select_related('bank_line').order_by('-transaction_date', '-id')

    # Apply Date Range Filters
    if start_date and end_date:
        base_queryset = base_queryset.filter(transaction_date__range=[start_date, end_date])

    if query:
        base_queryset = base_queryset.filter(
            Q(company_code__icontains=query) |
            Q(bank_line__transaction_description__icontains=query) |
            Q(recon_status__icontains=query)
        )

    paginator = Paginator(base_queryset, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    company_codes = [r.company_code for r in page_obj if r.company_code]
    mg_map = {
        item['a_company_code']: {'name': item['b_company_name'], 'agent': item['c_agent']}
        for item in UnityMgListing.objects.filter(a_company_code__in=company_codes).values('a_company_code', 'b_company_name', 'c_agent')
    }

    global_records = []
    for record in page_obj:
        remaining = record.transaction_amount - record.amount_settled
        mg_info = mg_map.get(record.company_code, {})
        
        global_records.append({
            'id': record.id,
            'transaction_date': record.transaction_date,
            'description': record.bank_line.transaction_description,
            'amount': record.transaction_amount,
            'settled': record.amount_settled,
            'remaining': remaining,
            'status': record.recon_status or "Unidentified",
            'company_code': record.company_code or "—",
            'company_name': mg_info.get('name', "Unassigned") if record.company_code else "—",
            'agent': mg_info.get('agent', "System") if record.company_code else "—",
        })

    context = {
        'page_obj': page_obj,
        'global_records': global_records,
        'search_query': query,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'unity_internal_app/global_bank.html', context)

@login_required
def export_global_bank_excel(request):
    """
    Exports the Global Bank history to Excel.
    FIXED: Attribute lookup for Agent.
    """
    query = request.GET.get('q')
    records = ReconnedBank.objects.select_related('bank_line').order_by('-transaction_date', '-id')

    if query:
        records = records.filter(
            Q(company_code__icontains=query) |
            Q(bank_line__transaction_description__icontains=query) |
            Q(recon_status__icontains=query)
        )

    company_codes = records.values_list('company_code', flat=True).distinct()
    mg_map = {
        item['a_company_code']: {
            'name': item['b_company_name'], 
            'agent': item['c_agent']
        }
        for item in UnityMgListing.objects.filter(a_company_code__in=company_codes).values('a_company_code', 'b_company_name', 'c_agent')
    }

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Global Bank Export"

    headers = ["Date", "Description", "Company Code", "Company Name", "Deposit Amount", "Settled Amount", "Remaining Balance", "Status", "Agent"]
    ws.append(headers)

    for r in records:
        mg_info = mg_map.get(r.company_code, {})
        ws.append([
            r.transaction_date,
            r.bank_line.transaction_description,
            r.company_code or "Unassigned",
            mg_info.get('name', "—"),
            r.transaction_amount,
            r.amount_settled,
            (r.transaction_amount - r.amount_settled),
            r.recon_status,
            mg_info.get('agent', "System") # FIXED
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Global_Bank_Export.xlsx"'
    wb.save(response)
    return response

@login_required
def download_attachment_view(request, message_id, attachment_id):
    """
    Acts as a proxy to download files from Microsoft Graph without 
    exposing the access token to the frontend.
    """
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    
    # Fetch the attachment data from Graph
    attachment_data = OutlookGraphService.get_attachment_raw(target_email, message_id, attachment_id)
    
    if 'error' in attachment_data:
        return HttpResponse("Error retrieving attachment from Microsoft.", status=400)

    # Graph returns the file content as a base64 encoded string
    file_content = base64.b64decode(attachment_data['contentBytes'])
    file_name = attachment_data.get('name', 'attachment')
    content_type = attachment_data.get('contentType', 'application/octet-stream')

    response = HttpResponse(file_content, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response

@login_required
def export_email_list(request):
    """
    Exports the Master Archive to Excel, applying date and category filters.
    """
    filter_type = request.GET.get('type', 'all')
    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    # 1. Fetch Data (Mirroring email_list_view logic)
    delegations_qs = EmailDelegation.objects.exclude(status='DLT')
    all_log_delegation_ids = DelegationTransactionLog.objects.values_list('delegation_id', flat=True)
    emails_with_replies = set(all_log_delegation_ids)
    inbox_map = {obj.email_id: obj for obj in OutlookInbox.objects.all()}

    # Process Delegations
    filtered_delegations = []
    for d in delegations_qs:
        has_reply = d.id in emails_with_replies
        should_show = (d.status == 'NEW') or (d.status == 'COM') or (d.status == 'DEL' and has_reply)
        
        if should_show:
            # Apply Date Filters to Delegations
            if start_date and d.received_at and d.received_at.date() < timezone.datetime.strptime(start_date, '%Y-%m-%d').date():
                continue
            if end_date and d.received_at and d.received_at.date() > timezone.datetime.strptime(end_date, '%Y-%m-%d').date():
                continue
            
            inbox_detail = inbox_map.get(d.email_id)
            d.subject = inbox_detail.subject if inbox_detail else "Unknown Subject"
            d.sender_address = inbox_detail.sender_address if inbox_detail else "Unknown"
            filtered_delegations.append(d)

    # Process Transactions
    transactions_qs = DelegationTransactionLog.objects.all()
    if start_date:
        transactions_qs = transactions_qs.filter(timestamp__date__gte=start_date)
    if end_date:
        transactions_qs = transactions_qs.filter(timestamp__date__lte=end_date)
    
    transactions = list(transactions_qs)

    # 2. Apply Category Filtering
    if filter_type == 'new':
        final_items = [d for d in filtered_delegations if d.status == 'NEW']
    elif filter_type == 'delegated':
        final_items = [d for d in filtered_delegations if d.status == 'DEL']
    elif filter_type == 'reply':
        final_items = transactions
    else:
        final_items = sorted(
            filtered_delegations + transactions,
            key=lambda x: x.received_at if hasattr(x, 'received_at') else x.timestamp,
            reverse=True
        )

    # 3. Create Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Email Archive"

    # Styling
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="43A047", end_color="43A047", fill_type="solid")
    
    headers = ['Status', 'Subject', 'Participant (From/To)', 'Date / Time', 'Assigned / Action By']
    ws.append(headers)

    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # 4. Populate Rows
    for item in final_items:
        if hasattr(item, 'action_type'): # It's a Transaction
            status = "Actioned"
            subject = item.subject
            participant = f"To: {item.recipient_email}"
            dt = item.timestamp.strftime('%Y-%m-%d %H:%M')
            user = item.user.username if item.user else "System"
        else: # It's a Delegation
            status = "Completed" if item.status == 'COM' else ("Delegated" if item.status == 'DEL' else "New")
            subject = item.subject
            participant = f"From: {item.sender_address}"
            dt = item.received_at.strftime('%Y-%m-%d %H:%M') if item.received_at else ""
            user = item.assigned_user.username if item.assigned_user else "Pending"

        ws.append([status, subject, participant, dt, user])

    # Adjust column widths
    for i, width in enumerate([15, 50, 30, 20, 20], 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    # 5. Return File
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Email_Archive_{timezone.now().strftime("%Y%m%d")}.xlsx'
    wb.save(response)
    return response