from base64 import urlsafe_b64decode, urlsafe_b64encode
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
from openpyxl.styles import Font, Alignment
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
from .models import BillSettlement, CreditNote, DelegationNote, DelegationTransactionLog, EmailDelegation, ImportBank, JournalEntry, ReconnedBank, ScheduleSurplus, UnityBill, UnityClaimNote, UnityMgListing, ClientNotes, InternalFunds, UnityNotes, UnityClaim
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
    "No change required / Review complete",
    "FX Difference identified",
    "Company Code corrected",
    "Fiscal Period corrected",
    "Query required - Further action pending",
    "Adjustment needed",
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
    """Displays the user dashboard."""
    username = request.user.username
    context = {
        'username': username,
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

@login_required
def unity_information(request: HttpRequest, company_code):
    """
    Displays detailed information for a single record.
    FIXED: Strict filtering by 'company_code' to ensure tasks move between dashboards 
    immediately after metadata updates.
    """
    
    # --- 1. Fetch Main Unity Record ---
    try:
        unity_record = UnityMgListing.objects.filter(a_company_code=company_code).first()
    except Exception:
        unity_record = None

    is_fallback = False
    lookup_code = company_code # This is the ID from the URL (e.g., '1510022')
    
    if not unity_record:
        unity_record = InternalFunds.objects.filter(A_Company_Code=company_code).first()
        if not unity_record:
            messages.error(request, f"Error: Record {company_code} not found.")
            return redirect('unity_list')
        is_fallback = True
        messages.warning(request, f"Full detail information is not available for {company_code}.")

    # --- 2. Fetch Related Data (Guaranteed Scope) ---
    notes = ClientNotes.objects.filter(a_company_code=company_code).order_by('-date')

    # --- Calculate Available Surplus ---
    company_bill_ids = UnityBill.objects.filter(C_Company_Code=lookup_code).values_list('id', flat=True)
    if company_bill_ids:
        total_created = ScheduleSurplus.objects.filter(
            unity_bill_source_id__in=company_bill_ids
        ).aggregate(total=Sum('surplus_amount'))['total'] or ZERO_DECIMAL

        surplus_ids = ScheduleSurplus.objects.filter(
            unity_bill_source_id__in=company_bill_ids
        ).values_list('id', flat=True)
        
        total_allocated = JournalEntry.objects.filter(
            surplus_source_id__in=surplus_ids
        ).aggregate(total=Sum('amount'))['total'] or ZERO_DECIMAL
        available_surplus_value = total_created - total_allocated
    else:
        available_surplus_value = ZERO_DECIMAL
    
    # --- Bankline Logic ---
    bank_lines_assigned = ReconnedBank.objects.filter(company_code=company_code).select_related('bank_line').order_by('-transaction_date')
    for line in bank_lines_assigned:
        total_settled_by_this_line = BillSettlement.objects.filter(
            reconned_bank_line_id=line.id
        ).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
        line.true_remaining_balance = line.transaction_amount - total_settled_by_this_line
        line.is_fully_consumed = (line.true_remaining_balance <= ZERO_DECIMAL)
        line.original_assigned_amount = line.transaction_amount 
    
    bank_lines = bank_lines_assigned
    credit_notes = CreditNote.objects.filter(member_group_code=company_code).order_by('-ccdates_month')

    try:
        company_claims = UnityClaim.objects.filter(company_code=company_code).prefetch_related('notes').order_by('-last_contribution_date', 'member_surname')
    except Exception:
        company_claims = []
    
    # --- 3. Fetch Communication Logs (Notes/Calls) ---
    try:
        communication_logs = UnityNotes.objects.filter(member_group_code=lookup_code).filter(~Q(communication_type='Sent Email')).order_by('-date')
    except Exception:
        communication_logs = []
    
    # --- 4. Build Unified Email History ---
    combined_email_log = []
    
    # 🛑 THE FIX: Query EmailDelegation strictly by the current 'company_code' field 🛑
    # This ensures that tasks moved from FAR0396 to 1510022 appear correctly.
    delegated_emails = EmailDelegation.objects.filter(
        company_code=lookup_code
    ).select_related('assigned_user').order_by('-received_at')

    for task in delegated_emails:
        combined_email_log.append({
            'type': 'Delegated',
            'display_type': task.get_status_display(),
            'subject': f"[TASK] {task.email_id} ({task.company_code})",
            'body': f"Status: {task.get_status_display()}",
            'timestamp': task.received_at,
            'action_user': f"System (via {settings.OUTLOOK_EMAIL_ADDRESS})",
            'assigned_to': task.assigned_user.username if task.assigned_user else 'UNASSIGNED',
            'badge_color': '#3f51b5',
            'icon': '📥',
            'email_id': task.email_id,
            'log_id': f'delegation-{task.id}',
        })
        
        # Transactions (Replies) associated with these tasks move with the task
        transactions = DelegationTransactionLog.objects.filter(delegation=task).select_related('user')
        for tx in transactions:
            combined_email_log.append({
                'type': 'Reply',
                'display_type': tx.action_type, # Displays custom destinations like "Sent to Sanlam"
                'subject': tx.subject,
                'timestamp': tx.timestamp,
                'action_user': tx.user.username if tx.user else 'System',
                'assigned_to': tx.recipient_email,
                'badge_color': '#f7931e',
                'icon': '📧',
                'log_id': f'transaction-{tx.id}',
            })
            
    # Direct Sent Emails from the UnityNotes table
    sent_emails_from_notes = UnityNotes.objects.filter(member_group_code=lookup_code, communication_type='Sent Email').order_by('-date')
    for log in sent_emails_from_notes:
        combined_email_log.append({
            'type': 'Direct Sent',
            'display_type': 'Direct Sent Email',
            'subject': log.action_notes or 'Email Sent',
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
        settled_sum = BillSettlement.objects.filter(unity_bill_source_id=bill.id).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
        bill.total_covered = settled_sum
        if bill.is_reconciled:
            bill.display_status = 'RECON COMPLETE'
            bill.bankline_total = BillSettlement.objects.filter(unity_bill_source_id=bill.id, reconned_bank_line_id__isnull=False).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
            bill.credit_allocated = BillSettlement.objects.filter(unity_bill_source_id=bill.id, source_credit_note_id__isnull=False).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
            bill.surplus_allocated_from_journals = JournalEntry.objects.filter(target_bill_id=bill.id).aggregate(total=Sum('amount'))['total'] or ZERO_DECIMAL
            bill.surplus_created = ScheduleSurplus.objects.filter(unity_bill_source_id=bill.id).aggregate(total=Sum('surplus_amount'))['total'] or ZERO_DECIMAL
            settled_bills.append(bill)
        else:
            bill.display_status = 'OPEN' if bill.total_covered > ZERO_DECIMAL else 'SCHEDULED'
            open_bills.append(bill)

    my_delegated_emails = EmailDelegation.objects.filter(assigned_user=request.user, status__in=['DEL', 'NEW']).order_by('-received_at')

    # --- 6. HANDLE POST REQUESTS ---
    if request.method == 'POST':
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
                
                # Send via Graph API
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
        'combined_email_log': combined_email_log, # Displays strictly mapped tasks
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
    """Displays a single reconciled bank line for review."""
    
    # 1. Check for the source of the navigation
    # This checks the query string. If the link used was: /review/32/?source=unity
    is_from_unity_info = request.GET.get('source') == 'unity'
    
    # Fetch data (unchanged)
    recon_record = get_object_or_404(ReconnedBank.objects.select_related('bank_line'), pk=recon_id)
    
    company_codes = InternalFunds.objects.values_list('A_Company_Code', flat=True).distinct().order_by('A_Company_Code')

    context = {
        'recon_record': recon_record,
        'bank_record': recon_record.bank_line,
        'company_codes': company_codes,
        'review_notes': REVIEW_NOTES_OPTIONS,
        'is_from_unity_info': is_from_unity_info, # <-- NEW CONTEXT VARIABLE
    }
    return render(request, 'unity_internal_app/display_bankline_review.html', context)

@login_required
@transaction.atomic
def update_bankline_details(request, recon_id):
    """Updates the ReconnedBank record details."""
    # Assuming ReconnedBank and other necessary modules are imported
    recon_record = get_object_or_404(ReconnedBank, pk=recon_id)
    
    # Store the original company code to check for changes
    original_company_code = recon_record.company_code
    
    if request.method == 'POST':
        new_company_code = request.POST.get('company_code_select')
        new_fiscal_date = request.POST.get('fiscal_date')
        review_note = request.POST.get('review_note')

        # 1. Update fields
        
        # Determine if allocation was cleared or changed
        allocation_cleared = (new_company_code in [None, '', 'None'])
        
        recon_record.company_code = new_company_code if new_company_code else None
        recon_record.fiscal_date = new_fiscal_date if new_fiscal_date else None
        recon_record.review_note = review_note
        
        old_status = recon_record.recon_status
        new_status = old_status # Default to current status
        
        # --- STATUS LOGIC ---

        if allocation_cleared:
            # Case 1: Company code is cleared (de-allocated).
            # Set status to None/empty string, making it 'Unidentified' in bank_list.html
            new_status = None
            
        elif recon_record.company_code:
            # Case 2: Company code is assigned (or remains assigned)
            
            if recon_record.fiscal_date:
                # Case 2b: Code and Date are assigned -> Final State
                new_status = 'Unreconciled - Allocated'
            else:
                # Case 2a: Code is assigned, but date is missing -> Intermediate State
                new_status = 'Unreconciled - Assigned'
        
        # Special check for 'Review Pending' (note takes precedence over general states)
        if review_note and "Query required" in review_note:
            new_status = 'Review Pending'
        
        # 2. Save new status and record
        
        if new_status != old_status:
            messages.info(request, f"Status updated from '{old_status or 'Unidentified'}' to '{new_status or 'Unidentified'}'.")

        # Ensure the field accepts None if needed, otherwise use an empty string
        recon_record.recon_status = new_status if new_status is not None else ''
        recon_record.save()

        # 3. Sync comments to the original bank line for visibility
        # Assuming bank_line relation exists via recon_record.bank_line
        bank_line = recon_record.bank_line
        bank_line.comments = f"Reviewed: {review_note} (Code: {recon_record.company_code or 'N/A'}, Status: {recon_record.recon_status or 'Unidentified'})"
        bank_line.save()
        
        messages.success(request, f"Bank Line {recon_id} details saved as '{recon_record.recon_status or 'Unreconciled - Unidentified'}'.")
        
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
    # Define a small tolerance for Decimal comparisons (e.g., 0.0001)
    SAFETY_TOLERANCE = Decimal('0.0001') 
    
    # Use the Decimal type for all monetary values
    bill_record = get_object_or_404(UnityBill, id=bill_id, C_Company_Code=company_code)
    
    # --- CALCULATE AVAILABLE DEBT (NEW FLEXIBLE LOGIC) ---
    available_debt_lines = get_available_bank_lines(company_code)
    total_debt = available_debt_lines.aggregate(total=Sum('remaining_debt'))['total'] or ZERO_DECIMAL
    
    # Fiscal period is now only used for display/context, not for filtering debt lines
    bill_date = bill_record.A_CCDatesMonth
    month_start_date = bill_date.replace(day=1)
    next_month = month_start_date + relativedelta(months=1)
    fiscal_end_date = next_month - relativedelta(days=1)
    # --- END NEW DEBT CALCULATION ---

    # --- AGGREGATIONS ---
    
    # 1. TOTAL APPLIED TO BILL: Get the true total from the unified audit ledger (BillSettlement)
    # This includes Cash, Credits, and Surpluses applied to THIS bill.
    total_applied = BillSettlement.objects.filter(
        unity_bill_source_id=bill_record.pk
    ).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
    
    # 2. AGGREGATE SEPARATION FOR DISPLAY (Metrics Row)
    
    # Get Credit Total (Settlements linked to a Credit Note ID)
    total_credit_notes_assigned = BillSettlement.objects.filter(
        unity_bill_source_id=bill_record.pk,
        source_credit_note_id__isnull=False
    ).aggregate(total_credit=Sum('settled_amount'))['total_credit'] or ZERO_DECIMAL

    # --- MATH UPDATES ---
    total_covered = total_applied
    scheduled_amount = bill_record.H_Schedule_Amount or ZERO_DECIMAL
    
    remaining_scheduled_amount = scheduled_amount - total_covered
    
    # Logic for Over-scheduled amount (if debt exceeds the remaining scheduled amount)
    over_scheduled_amount = max(ZERO_DECIMAL, total_debt - max(ZERO_DECIMAL, remaining_scheduled_amount))
    
    # Cap the remaining schedule at zero for the final outstanding calculation
    capped_remaining_schedule = max(ZERO_DECIMAL, remaining_scheduled_amount)
    
    # Current Outstanding is the Debt remaining after it satisfies the remaining Schedule
    current_outstanding = total_debt - capped_remaining_schedule

    # --- FIND AVAILABLE SURPLUS FOR THIS COMPANY (Manual Allocation Tool) ---
    company_bill_ids = UnityBill.objects.filter(C_Company_Code=company_code).values_list('id', flat=True)
    potential_surpluses = ScheduleSurplus.objects.filter(
        unity_bill_source_id__in=company_bill_ids
    ).exclude(status='FULLY_APPLIED')
    
    available_surpluses = []
    total_available_surplus_value = ZERO_DECIMAL
    
    for s in potential_surpluses:
        # Calculate how much of *this specific* surplus is used from JournalEntry records
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
    # Fetch Journal Entries where THIS bill is the target (i.e., this bill *consumed* the surplus)
    applied_journals = JournalEntry.objects.filter(target_bill=bill_record).select_related('surplus_source')
    
    # Calculate the sum for the 'Surplus Allocated (Used)' metric card and table footer
    total_surplus_applied_to_bill = applied_journals.aggregate(
        total_footer=Sum('amount')
    )['total_footer'] or ZERO_DECIMAL
    
    # -------------------------------------------------------------
    # --- UPDATED ACTION MESSAGE LOGIC (WITH TOLERANCE FIX) ---
    # -------------------------------------------------------------
    
    # Check if the bill is fully covered (scheduled_amount <= total_covered + small safety margin)
    is_bill_fully_covered = total_covered >= (scheduled_amount - SAFETY_TOLERANCE)
    
    if is_bill_fully_covered:
        is_proceed_enabled = True
        # If the bill is covered, use the precise settled amount for the message
        settled_vs_scheduled_diff = total_covered - scheduled_amount
        
        if settled_vs_scheduled_diff >= SAFETY_TOLERANCE:
             # Over-covered (Surplus/Credit/Cash applied more than needed)
             action_message = f"FULLY COVERED by Settlements. R{settled_vs_scheduled_diff:.2f} recorded as surplus. Ready for Final Recon/Closure."
        else:
             # Exactly covered (within tolerance)
             action_message = "PERFECTLY COVERED by Settlements. Ready for Final Recon/Closure."

    elif total_debt > ZERO_DECIMAL: 
        # Partial coverage, but there is cash available for allocation
        is_proceed_enabled = False # Keep Proceed button disabled until schedule is met
        
        # Determine if available debt can cover the remaining schedule
        if total_debt >= remaining_scheduled_amount:
             action_message = f"FULL CASH COVERAGE AVAILABLE: Available Cash (R{total_debt:.2f}) can clear the Remaining Schedule (R{remaining_scheduled_amount:.2f})."
             is_proceed_enabled = True # Enable if remaining cash is sufficient
        else:
             action_message = f"Partial coverage available. R{total_debt:.2f} can be applied to the remaining liability of R{remaining_scheduled_amount:.2f}."
             
    else: 
        # No debt available and bill is not covered
        is_proceed_enabled = False
        action_message = f"Action REQUIRED: R{remaining_scheduled_amount:.2f} liability remains. Settlement is unavailable until more debt is applied or the schedule is manually reduced."

    # -------------------------------------------------------------
    
    context = {
        'bill_record': bill_record,
        'company_code': company_code,
        'total_debt': total_debt, # Total available for the company (new definition)
        'scheduled_amount': scheduled_amount,
        
        # Aggregates (Mapped to new metric cards)
        'total_credit_notes_assigned': total_credit_notes_assigned,
        'total_available_surplus': total_available_surplus_value,
        
        # Logic
        'remaining_schedule_amount': remaining_scheduled_amount,
        'current_outstanding': current_outstanding, # Surplus after covering remaining schedule
        'over_scheduled_amount': over_scheduled_amount,
        
        # Lists
        'all_lines': available_debt_lines.all().order_by('transaction_date'), # NEW: Pass all available lines
        'credit_notes': CreditNote.objects.filter(assigned_unity_bill=bill_record),
        
        # NEW CONTEXT
        'available_surpluses': available_surpluses,
        'applied_journals': applied_journals,
        'total_journal_assigned': total_surplus_applied_to_bill,
        
        'action_message': action_message,
        'is_proceed_enabled': is_proceed_enabled,
        'fiscal_starting_date': month_start_date, # Only for display context
        'fiscal_closing_date': fiscal_end_date, # Only for display context
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
    Handles the cash allocation and bank line splitting/consumption logic.
    CRITICAL FIX: Retains company_code on the CONSUMED segment when splitting 
    to preserve audit history and correct split remainder pushback.
    """
    # Ensure all necessary imports are available at the top of views.py:
    # from django.db import connection, transaction
    # from django.db.models import Sum, F
    # from django.urls import reverse
    # from django.utils import timezone
    # from decimal import Decimal
    # from django.shortcuts import render, redirect, get_object_or_404
    # from .models import BillSettlement, ReconnedBank, UnityBill, ScheduleSurplus 
    # from .models import ZERO_DECIMAL # Assumed defined globally
    
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)

    aware_dt = timezone.now()
    
    selected_recon_id = request.POST.get('selected_recon_id')
    amount_to_apply_str = request.POST.get('amount_to_apply')
    
    # CRITICAL FIX: The front-end checkbox sends 'True' or nothing.
    should_split_and_reallocate = request.POST.get('split_and_reallocate') == 'True' 
    
    # --- Input Validation (Retained) ---
    if not selected_recon_id:
        messages.error(request, "Allocation failed: You must select a Bank Line to apply cash from.")
        return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)
        
    if not amount_to_apply_str or amount_to_apply_str.strip() == '':
        messages.error(request, "Allocation failed: You must specify an amount to apply (R 0.01 minimum).")
        return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)
        
    try:
        amount_to_apply = Decimal(amount_to_apply_str) 
        
        if amount_to_apply <= ZERO_DECIMAL:
            messages.error(request, "Allocation failed: Amount must be greater than zero.")
            return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)
            
        # Lock both the Source (ReconnedBank) and Target (UnityBill)
        recon_line = ReconnedBank.objects.select_for_update().get(pk=selected_recon_id, company_code=company_code)
        bill_record = UnityBill.objects.select_for_update().get(pk=bill_id, C_Company_Code=company_code)
        
        # 1. Calculate remaining capacity on the Source Bank Line
        line_unsettled = recon_line.transaction_amount - recon_line.amount_settled
        if amount_to_apply > line_unsettled:
            messages.error(request, f"Allocation failed: Only R{line_unsettled:.2f} remains on this bank line.")
            return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)
            
        # 2. Calculate remaining liability on the Bill (target capacity)
        bill_settled_agg = BillSettlement.objects.filter(unity_bill_source_id=bill_record.pk).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
        bill_remaining_liability = bill_record.H_Schedule_Amount - bill_settled_agg
        
        # 3. Enforce soft cap: Do not allocate more than the bill needs
        final_amount_applied = min(amount_to_apply, bill_remaining_liability)
        
        if final_amount_applied <= ZERO_DECIMAL:
            messages.warning(request, "This bill is already settled or the applied amount is zero. Allocation not performed.")
            return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)
            
        # 4. Create the Audit Trail (BillSettlement - The Data Cube Fact)
        BillSettlement.objects.create(
            reconned_bank_line=recon_line,
            unity_bill_source=bill_record,
            settled_amount=final_amount_applied,
            settlement_date=aware_dt,
            source_credit_note_id=None,
            source_journal_entry_id=None,
            confirmed_by=request.user,
            
            # --- ADDITION FOR DIRECT IMPORTBANK TRACEABILITY ---
            original_import_bank_id=recon_line.bank_line_id,
            # ---------------------------------------------------
        )
        
        # 5. Consume the Source (ReconnedBank)
        recon_line.amount_settled += final_amount_applied
        
        # 6. SPLIT/UNASSIGN LOGIC (FIX APPLIED)
        amount_left_on_source = recon_line.transaction_amount - recon_line.amount_settled
        
        original_company_code = recon_line.company_code # Preserve the originally assigned code
        original_bank_line_pk = recon_line.bank_line_id
        original_transaction_date = recon_line.transaction_date
        
        if amount_left_on_source > ZERO_DECIMAL:
            if should_split_and_reallocate:
                # 6a. SPLIT: Create NEW segment for remainder (Pushed-back portion)
                new_line = ReconnedBank.objects.create(
                    bank_line_id=original_bank_line_pk,
                    company_code=None,  # CRITICAL: NULL company_code for pushback
                    transaction_amount=amount_left_on_source,
                    transaction_date=original_transaction_date,
                    fiscal_date=None, 
                    recon_status='Unreconciled - New Source', # Pushback Status
                    amount_settled=ZERO_DECIMAL,
                )
                
                # Close the ORIGINAL line (Consumed portion)
                recon_line.transaction_amount = recon_line.amount_settled # Reduce amount to portion consumed
                recon_line.recon_status = 'Reconciled'
                # recon_line.company_code is implicitly retained from the line above (recon_line = ReconnedBank.objects.get(...) ) 
                
                messages.info(request, f"Bank line split. R{final_amount_applied:.2f} applied to bill. R{amount_left_on_source:.2f} now available for re-assignment (Segment {new_line.id}).")

            else:
                # 6b. NO SPLIT: Remainder stays assigned.
                recon_line.recon_status = 'Partially Reconciled'
                # company_code remains original_company_code
                messages.info(request, f"R{final_amount_applied:.2f} applied to bill. R{amount_left_on_source:.2f} remains assigned to {company_code}.")
        
        else: # amount_left_on_source <= ZERO_DECIMAL
            # 6c. Fully Consumed
            recon_line.recon_status = 'Reconciled'
            # CRITICAL FIX: RETAIN CODE FOR AUDIT TRACE
            # company_code remains original_company_code
            messages.info(request, f"Bank Line {recon_line.id} fully consumed and reconciled to {original_company_code}.")

        recon_line.save() # Save the updated state of the consumed segment
        
        # 7. Surplus Check (Retained)
        new_settled_total = bill_settled_agg + final_amount_applied
        remaining_after_settlement = bill_record.H_Schedule_Amount - new_settled_total
        
        # Check if Bill is overpaid -> create ScheduleSurplus
        if remaining_after_settlement < ZERO_DECIMAL:
            surplus_amount = abs(remaining_after_settlement)
            ScheduleSurplus.objects.create(
                unity_bill_source_id=bill_record.pk,
                surplus_amount=surplus_amount,
                creation_date=aware_dt.date(),
                status='UNAPPLIED'
            )
            messages.warning(request, f"Excess Net Funds of R{surplus_amount:.2f} recorded as a Schedule Surplus from this cash allocation.")
            
        # Check if Bill is paid (latch message)
        if new_settled_total >= bill_record.H_Schedule_Amount:
            messages.success(request, f"Allocation successful. The bill is now fully covered (R{new_settled_total:.2f} settled). Click **Proceed to Recon (Finalize)** to close the bill.")
        else:
            messages.success(request, f"R{final_amount_applied:.2f} successfully applied to Bill #{bill_id}. Continue allocation if necessary.")

        # 8. Redirect back to the summary
        url = reverse('pre_bill_reconciliation_summary', kwargs={'company_code': company_code, 'bill_id': bill_id})
        return redirect(f"{url}?cache={aware_dt.timestamp()}")
        
    except ReconnedBank.DoesNotExist:
        messages.error(request, f"Allocation failed: Bank Line {selected_recon_id} not found or does not belong to company {company_code}.")
        return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)
    except Decimal.InvalidOperation:
        messages.error(request, "Allocation failed: Invalid amount entered. Please use numerical digits only.")
        return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)
    except Exception as e:
        messages.error(request, f"An unexpected error occurred during allocation: {e}")
        return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)

@login_required
@transaction.atomic
def finalize_reconciliation(request, company_code, bill_id):
    """
    Handles the final step of reconciliation (clicking the 'Proceed to Recon' button).
    It checks if the bill is balanced and flips the is_reconciled flag, 
    then redirects to the final reconciled summary page.
    """
    try:
        bill_record = UnityBill.objects.select_for_update().get(pk=bill_id, C_Company_Code=company_code)
        
        bill_settled_agg = BillSettlement.objects.filter(unity_bill_source_id=bill_record.pk).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
        
        if bill_settled_agg >= bill_record.H_Schedule_Amount:
            if not bill_record.is_reconciled:
                bill_record.is_reconciled = True
                bill_record.save()
                messages.success(request, f"Bill #{bill_id} successfully finalized and marked as **RECONCILED**.")
                
                # --- FIX APPLIED HERE: REDIRECT TO FINAL SUCCESS URL ---
                return redirect('reconciliation_success_view', company_code=company_code, bill_id=bill_id)

            else:
                messages.info(request, "Bill is already reconciled.")
        else:
            remaining_liability = bill_record.H_Schedule_Amount - bill_settled_agg
            messages.error(request, f"Finalization blocked. R{remaining_liability:.2f} of the schedule remains uncovered.")

        return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)

    except UnityBill.DoesNotExist:
        messages.error(request, f"Bill {bill_id} not found.")
        return redirect('unity_information', company_code=company_code)
    except Exception as e:
        messages.error(request, f"An unexpected error occurred during finalization: {e}")
        return redirect('pre_bill_reconciliation_summary', company_code=company_code, bill_id=bill_id)
    
@login_required
def reconciliation_success_view(request, company_code, bill_id):
    """
    Renders the confirmation/final summary page after successful reconciliation.
    Gathers all required context for finalize_reconciliation.html (which is now 
    the final success page).
    """
    bill_record = get_object_or_404(UnityBill, id=bill_id, C_Company_Code=company_code)
    
    # --- Data Aggregation ---
    
    # 1. Settled Totals
    total_settled_against_bill = BillSettlement.objects.filter(unity_bill_source_id=bill_record.pk).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
    total_credit_assigned = BillSettlement.objects.filter(unity_bill_source_id=bill_record.pk, source_credit_note_id__isnull=False).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
    
    # 2. Bank Lines used for settlement (used for the table display)
    lines_to_settle = get_bank_lines_used_in_settlement(bill_record) 
    
    # 3. Fiscal Dates 
    # Assumes Bill record has a date field called A_CCDatesMonth
    bill_date = bill_record.A_CCDatesMonth
    month_start_date = bill_date.replace(day=1)
    fiscal_starting_date = month_start_date 
    # Assuming relativedelta is available/imported
    fiscal_closing_date = month_start_date + relativedelta(months=1) - relativedelta(days=1)
    
    # 4. Final Math
    scheduled_amount = bill_record.H_Schedule_Amount - total_settled_against_bill # Should be 0.00 or near zero
    total_scheduled_amount_initial = bill_record.H_Schedule_Amount
    
    # total_debt represents the total funds applied (total_settled_against_bill)
    total_debt = total_settled_against_bill
    
    # --- Context Setup ---
    context = {
        'company_code': company_code,
        'bill_record': bill_record,
        
        # Data required by finalize_reconciliation.html
        'lines_to_settle': lines_to_settle, 
        'total_debt': total_debt,
        'total_scheduled_amount_initial': total_scheduled_amount_initial,
        'total_settled_against_bill': total_settled_against_bill,
        'total_credit_assigned': total_credit_assigned,
        'scheduled_amount': scheduled_amount, # Remaining schedule (should be 0)
        
        'fiscal_starting_date': fiscal_starting_date,
        'fiscal_closing_date': fiscal_closing_date,

        'warning_message': 'This bill is permanently closed and reconciled.', 
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
    Displays a list of all imported CreditNote records awaiting assignment.
    """
    credit_notes = CreditNote.objects.all().order_by('-processed_date')
    
    context = {
        'page_title': 'Credit Note Records Awaiting Fiscal Date',
        'credit_notes': credit_notes,
    }
    
    return render(request, 'unity_internal_app/credit_note_list.html', context)

@login_required
@transaction.atomic
def assign_fiscal_date_view(request, note_id):
    """
    Assigns fiscal date and links a CreditNote to a UnityBill. 
    FIX: Updates the math (BillSettlement), but DOES NOT auto-close the bill.
    The bill remains OPEN until the user manually clicks 'Proceed to Recon'.
    """
    from django.contrib import messages
    from django.shortcuts import redirect, get_object_or_404
    from django.urls import reverse
    from django.utils import timezone
    from decimal import Decimal
    from django.db.models import Sum
    from datetime import datetime
    from .models import CreditNote, UnityBill, BillSettlement, ScheduleSurplus
    from .forms import FiscalDateAssignmentForm

    context_type = request.GET.get('context', 'info')
    
    note_record = get_object_or_404(CreditNote, id=note_id)
    company_code = note_record.member_group_code
    
    redirect_bill_id = request.GET.get('bill_id')
    
    # --- Cleanup: Delete old BillSettlement for this note ---
    BillSettlement.objects.filter(source_credit_note_id=note_id).delete()
    
    if request.method == 'POST':
        form = FiscalDateAssignmentForm(request.POST,
                                         instance=note_record,
                                         company_code=company_code,
                                         context_type=context_type)
        
        if form.is_valid():
            note = form.save(commit=False)
            user_selected_bill = form.cleaned_data.get('target_bill_id')
            new_fiscal_date = form.cleaned_data.get('fiscal_date')
            bill_to_process = user_selected_bill
            
            # --- 1. Auto-Allocation Logic ---
            if new_fiscal_date and bill_to_process is None:
                try:
                    # UPDATED SEARCH: Match Year/Month & is_reconciled=False
                    open_bill = UnityBill.objects.filter(
                        C_Company_Code=company_code,
                        A_CCDatesMonth__year=new_fiscal_date.year,
                        A_CCDatesMonth__month=new_fiscal_date.month,
                        is_reconciled=False
                    ).first()
                    
                    if open_bill:
                        bill_to_process = open_bill
                        messages.success(request, f"Credit auto-assigned to Bill ID {open_bill.id}.")
                    else:
                        messages.warning(request, f"Fiscal Date set, but no OPEN Bill found matching that month.")
                except Exception as e:
                    messages.error(request, f"Auto-allocation failed: {e}")

            # --- 2. Set Assignment ---
            if bill_to_process:
                # 2A. Assignment & Save
                note.assigned_unity_bill = bill_to_process
                redirect_bill_id = bill_to_process.id
                note.save()
                
                # 2B. Create BillSettlement entry (Updates the Math ONLY)
                aware_dt = timezone.now()
                BillSettlement.objects.create(
                    reconned_bank_line=None,
                    unity_bill_source=bill_to_process,
                    settled_amount=note.schedule_amount,
                    settlement_date=aware_dt,
                    source_credit_note_id=note.id,
                    source_journal_entry_id=None
                )

                # 2C. Surplus Check
                # (WE REMOVED THE AUTO-CLOSE LOGIC HERE)
                
                total_settled = BillSettlement.objects.filter(
                    unity_bill_source_id=bill_to_process.pk
                ).aggregate(total=Sum('settled_amount'))['total'] or ZERO_DECIMAL
                
                remaining_schedule = bill_to_process.H_Schedule_Amount - total_settled
                
                if total_settled >= bill_to_process.H_Schedule_Amount:
                    # Just notify the user, DO NOT CLOSE
                    messages.success(request, f"Credit Assigned. Bill #{bill_to_process.id} is now balanced (R0.00). It is ready for Final Recon.")
                else:
                    messages.success(request, f"Credit applied. Remaining Debt: R{remaining_schedule:.2f}")

                # Handle Surplus if overpaid
                if remaining_schedule < ZERO_DECIMAL:
                    surplus_amount = abs(remaining_schedule)
                    ScheduleSurplus.objects.create(
                        unity_bill_source_id=bill_to_process.pk,
                        surplus_amount=surplus_amount,
                        creation_date=timezone.now().date(),
                        generating_credit_note_id=note.pk,
                        status='UNAPPLIED'
                    )
                    messages.warning(request, f"Credit Note created a Surplus of R{surplus_amount:.2f}.")
                
            else:
                # Unassign logic
                if note.assigned_unity_bill_id:
                    ScheduleSurplus.objects.filter(generating_credit_note_id=note.pk).delete()
                note.assigned_unity_bill = None
                note.save()
            
            # Final message and Redirect
            timestamp = timezone.now().timestamp()
            
            if context_type == 'summary' and redirect_bill_id:
                return redirect(f"{reverse('pre_bill_reconciliation_summary', kwargs={'company_code': company_code, 'bill_id': redirect_bill_id})}?cache={timestamp}")
            else:
                return redirect(f"{reverse('unity_billing_history', kwargs={'company_code': company_code})}?cache={timestamp}#credit")
        else:
            messages.error(request, "Error saving assignment. Please check all fields.")
            
    else:
        # GET request
        initial_data = {}
        if note_record.assigned_unity_bill:
            initial_data['target_bill_id'] = note_record.assigned_unity_bill
        
        form = FiscalDateAssignmentForm(instance=note_record,
                                         company_code=company_code,
                                         initial=initial_data,
                                         context_type=context_type)

    context = {
        'page_title': f'Assign Fiscal Date & Bill: Record {note_id}',
        'note': note_record,
        'form': form,
        'company_code': company_code,
        'context_type': context_type,
    }
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
    Renders a template showing a high-level overview of ALL Bill History.
    UPDATED: Determines 'RECON' status based on the is_reconciled flag, 
    not just the math.
    """
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
        messages.error(request, "Invalid date format provided for filtering.")
        
    T1_TABLE = 'bill_settlement'
    
    filtered_bill_ids = set()

    # --- 1. Determine Bill IDs to Display (Filtering Bills by Settlement Date) ---
    if filter_start_date or filter_end_date:
        
        # 1A. Filter by Cash Settlement Date (bill_settlement table)
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
            messages.error(request, f"Database Error during cash settlement filter: {e}")
            
        # 1B. Filter by Journal Entry/Surplus Allocation Date (JournalEntry model)
        journal_queryset = JournalEntry.objects.all()
        if filter_start_date:
            journal_queryset = journal_queryset.filter(allocation_date__gte=filter_start_date)
        if filter_end_date:
            journal_queryset = journal_queryset.filter(allocation_date__lte=filter_end_date)
        journal_ids = journal_queryset.values_list('target_bill_id', flat=True).distinct()
        filtered_bill_ids.update(journal_ids)
        
        final_ids = list(filtered_bill_ids)

        if not final_ids:
            all_bills_queryset = UnityBill.objects.none()
        else:
            # Only include bills that match the ID list
            all_bills_queryset = UnityBill.objects.filter(id__in=final_ids)
            
    else:
        # No date filter: Show all bills
        all_bills_queryset = UnityBill.objects.all()

    # Prefetch related data for efficiency
    all_bills = list(all_bills_queryset.order_by('-A_CCDatesMonth', 'C_Company_Code'))
    filtered_bill_ids = [bill.id for bill in all_bills]
    
    # --- 2. Fetch Granular Settlements (Cash & Journal Entries) ---
    if not filtered_bill_ids:
        final_records = []
    else:
        id_placeholders = ', '.join(['%s'] * len(filtered_bill_ids))
        
        T2_TABLE = 'reconned_bank'
        T3_TABLE = 'importbank'

        # 2A. Fetch Cash Deposits (from BillSettlement)
        sql_query_cash = f"""
        SELECT
            T1.unity_bill_source_id, T3.DATE, T1.settled_amount
        FROM
            {T1_TABLE} T1
        LEFT JOIN
            {T2_TABLE} T2 ON T1.reconned_bank_line_id = T2.bank_line_id
        LEFT JOIN
            {T3_TABLE} T3 ON T2.bank_line_id = T3.id
        WHERE
            T1.unity_bill_source_id IN ({id_placeholders})
        ORDER BY
            T1.unity_bill_source_id, T3.DATE
        """
        deposits_by_bill = defaultdict(list)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql_query_cash, filtered_bill_ids)
                raw_results = cursor.fetchall()
        except Exception as e:
            messages.error(request, f"Database Error during cash deposit fetch: {e}")
            raw_results = []
    
        for row in raw_results:
            bill_id = row[0]
            deposit_date = row[1]
            deposit_amount = row[2]
            # Only include non-Journal rows (where we found a date from importbank)
            if deposit_date:
                deposits_by_bill[bill_id].append({'date': deposit_date, 'amount': deposit_amount, 'type': 'Cash'})
            
        # 2B. Fetch Journal Entries (Surplus Allocations)
        journal_queryset = JournalEntry.objects.filter(target_bill__in=filtered_bill_ids).select_related('surplus_source')
        
        for je in journal_queryset:
            deposits_by_bill[je.target_bill_id].append({
                'date': je.allocation_date,
                'amount': je.amount,
                'type': 'Journal',
            })
            
        # 2C. Fetch Credits for Total Calculation
        # (Note: We still need this to show the total settled amount, even if status is flag-based)
        credit_notes_agg = BillSettlement.objects.filter(
            unity_bill_source_id__in=filtered_bill_ids,
            source_credit_note_id__isnull=False
        ).values('unity_bill_source_id').annotate(
            total_credit=Sum('settled_amount')
        )
        credits_map = {item['unity_bill_source_id']: item['total_credit'] for item in credit_notes_agg}
    
        # --- 3. Consolidate Data and CHECK FLAG ---
        
        final_records = []
        
        for bill in all_bills:
            deposits = deposits_by_bill.get(bill.id, [])
            
            # 3A. AGGREGATE TOTALS (For display purposes)
            cash_journal_settled = sum((d['amount'] for d in deposits), start=ZERO_DECIMAL)
            credit_settled = credits_map.get(bill.id, ZERO_DECIMAL)
            total_covered = cash_journal_settled + credit_settled
            
            # 3B. STATUS CHECK (UPDATED TO USE LATCH FLAG)
            if bill.is_reconciled:
                status_name = 'RECON COMPLETE'
                status_class = 'badge-success'
            else:
                status_name = 'OPEN'
                status_class = 'badge-danger'
            
            # If you want to show EVERYTHING (Open and Closed) so you can see history:
            final_records.append({
                'bill': bill,
                'deposits': deposits,
                'status_name': status_name,
                'status_class': status_class,
                'is_settled': bill.is_reconciled,
                'total_settled': total_covered,
            })

    # --- 4. Render HTML Template ---
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
    Displays bills ready for daily confirmation review, linking main bill data 
    with their associated bank lines AND credit notes for auditing.
    
    Sorting: By Final Date (J_Final_Date) Ascending, then Company Code, to match
    the specific grouped display required.
    
    Filtering: Applies to Final Date (J_Final_Date).
    UPDATED: Only shows reconciled bills (is_reconciled=True).
    """
    
    # 1. Date Filtering (No longer defaults to last 30 days)
    filter_start_date_str = request.GET.get('start_date')
    filter_end_date_str = request.GET.get('end_date')

    # Base Query: Order by 'Final Date' (Ascending), then 'Company Code'
    bills_queryset = UnityBill.objects.all().order_by('J_Final_Date', 'C_Company_Code')
    
    # NEW FILTER: Only include bills that are fully reconciled/closed
    bills_queryset = bills_queryset.filter(is_reconciled=True)

    if filter_start_date_str:
        try:
            start_dt = datetime.strptime(filter_start_date_str, '%Y-%m-%d').date()
            # Filter based on J_Final_Date
            bills_queryset = bills_queryset.filter(J_Final_Date__gte=start_dt)
        except ValueError:
            pass

    if filter_end_date_str:
        try:
            end_dt = datetime.strptime(filter_end_date_str, '%Y-%m-%d').date()
            # Filter based on J_Final_Date
            bills_queryset = bills_queryset.filter(J_Final_Date__lte=end_dt)
        except ValueError:
            pass
            
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
                    # Assumes CreditNote is imported
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

        # Use 0 if 'zero' is not defined/imported
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
    Calculates a 3% Admin Fee per bill line.
    
    UPDATED: Only shows reconciled bills (is_reconciled=True).
    """
    filter_start_date = request.GET.get('start_date')
    filter_end_date = request.GET.get('end_date')

    # Order by CC Dates Month, then by Company Code
    bills_queryset = UnityBill.objects.all().order_by('-A_CCDatesMonth', 'C_Company_Code')
    
    # NEW FILTER: Only include bills that are fully reconciled/closed
    bills_queryset = bills_queryset.filter(is_reconciled=True)


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
    
    # Process each bill individually (line-by-line)
    for bill in bills_queryset:
        
        # Use Decimal('0.00') if 'zero' is not defined/imported
        schedule_amount = bill.H_Schedule_Amount if bill.H_Schedule_Amount is not None else Decimal('0.00')
        active_members = bill.E_Active_Members or 0 
        
        # Calculate 3% Admin Fee on this specific bill's schedule
        admin_fee = schedule_amount * Decimal('0.03')
        
        # Find the FIRST settlement record for the bill
        first_settlement = BillSettlement.objects.filter(
            unity_bill_source_id=bill.pk
        ).order_by('settlement_date').first()
        
        posted_date = first_settlement.settlement_date if first_settlement else None
        
        posted_user = "N/A"
        if first_settlement and first_settlement.confirmed_by:
            # Assuming 'confirmed_by' is a ForeignKey to a User model
            posted_user = first_settlement.confirmed_by.username
        
        # Determine the Fiscal Period key (e.g., "2025-12")
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

@login_required
def save_claim(request, company_code):
    """
    Handles adding or editing a claim record from the Company Dashboard.
    Includes logic to save Claim Notes history.
    """
    if request.method == 'POST':
        # Get existing record if editing
        claim_id = request.POST.get('claim_id')
        if claim_id:
            claim_instance = get_object_or_404(UnityClaim, pk=claim_id)
            form = UnityClaimForm(request.POST, instance=claim_instance)
        else:
            form = UnityClaimForm(request.POST)

        if form.is_valid():
            # 1. Save the Claim
            saved_claim = form.save()

            # 2. [NEW] Handle Claim Notes Logic
            note_selection = request.POST.get('note_selection')
            note_description = request.POST.get('note_description')

            # Only save a note if the user actually selected or typed something
            if note_selection or (note_description and note_description.strip()):
                UnityClaimNote.objects.create(
                    claim=saved_claim,
                    note_selection=note_selection,
                    note_description=note_description,
                    created_by=request.user
                )
                messages.success(request, "Claim saved and Note added successfully.")
            else:
                messages.success(request, "Claim saved successfully.")
        else:
            # If form is invalid, print errors
            messages.error(request, f"Error saving claim: {form.errors}")
            
    # Redirect back to the Unity Info page, specifically the Claims tab
    return redirect(f"{reverse('unity_information', kwargs={'company_code': company_code})}#company-claims")


@login_required
def global_claims_view(request):
    """
    Dashboard view for searching all claims across the system.
    """
    # 1. Handle Search
    query = request.GET.get('q')
    if query:
        claims = UnityClaim.objects.filter(
            Q(id_number__icontains=query) | 
            Q(member_surname__icontains=query) | 
            Q(company_code__icontains=query)
        )
    else:
        # Limit to recent 50 for speed
        claims = UnityClaim.objects.all().order_by('-claim_created_date')[:50] 

    # 2. Fetch Companies for the "New Claim" Dropdown
    # We select only the fields we need to make the page lighter
    all_companies = UnityMgListing.objects.values('a_company_code', 'b_company_name', 'c_agent')

    context = {
        'claims': claims,
        'all_companies': all_companies # Pass this to the template
    }
    return render(request, 'unity_internal_app/global_claims.html', context)


@login_required
def save_global_claim(request):
    """
    Handles saving a claim from the Global Dashboard where Company Code is submitted in the form.
    """
    if request.method == 'POST':
        # 1. Check if we are Editing or Creating
        claim_id = request.POST.get('claim_id')
        
        if claim_id:
            # EDIT MODE: Fetch the existing instance so Django knows to UPDATE it
            claim_instance = get_object_or_404(UnityClaim, pk=claim_id)
            form = UnityClaimForm(request.POST, instance=claim_instance)
        else:
            # CREATE MODE: No ID, so create a new instance
            form = UnityClaimForm(request.POST)

        if form.is_valid():
            saved_claim = form.save()

            # 2. Handle Claim Notes (Copied from your save_claim logic)
            note_selection = request.POST.get('note_selection')
            note_description = request.POST.get('note_description')

            # Only save a note if the user actually selected or typed something
            if note_selection or (note_description and note_description.strip()):
                UnityClaimNote.objects.create(
                    claim=saved_claim,
                    note_selection=note_selection,
                    note_description=note_description,
                    created_by=request.user
                )
                messages.success(request, "Claim saved and Note added successfully.")
            else:
                messages.success(request, "Claim saved successfully.")
        else:
            messages.error(request, f"Error saving claim: {form.errors}")
            
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
    inbox_data = OutlookGraphService.fetch_inbox_messages(target_email, top_count=10) 
    
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
        
        # 🛑 FIX 4: Define 'method' and 'email_data' (which is None for GET) 🛑
        method = 'GET'
        email_data = None 
        
        # Line 3258 (Approximate):
        response = OutlookGraphService._make_graph_request(endpoint, target_email, method=method, data=email_data)
        
        # 🛑 FIX 5: Change 'email_data' to 'response' in the check 🛑
        if 'error' not in response:
            email_data = response # Use the response data
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
    return render(request, 'unity_internal_app/outlook_delegated_box.html', context)


@login_required
def outlook_delegated_action(request, delegation_id):
    """
    Handles Notes, Replies, Metadata Updates, and RESTORATION from Recycle Bin.
    Synchronized with CRM Unity logic to allow multi-purpose task management.
    """
    delegation = get_object_or_404(EmailDelegation, pk=delegation_id)
    
    # --- ROLE-BASED ACCESS CONTROL ---
    # Allow the assigned agent OR a manager (omega/superuser) to view the task.
    # Note: For recycled tasks (work_related=False), assigned_user is often None, 
    # so manager access is required to view them.
    is_manager = request.user.username.lower() == 'omega' or request.user.is_superuser
    
    if not is_manager and delegation.assigned_user != request.user:
        messages.error(request, "Access restricted. You are not assigned to this task.")
        return redirect('outlook_delegated_box')

    target_email = settings.OUTLOOK_EMAIL_ADDRESS 

    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        # --- 1. HANDLE RESTORE (Moves item from Recycle Bin back to Live Inbox) ---
        if action_type == 'restore_to_inbox':
            delegation.work_related = True
            delegation.status = 'NEW'       # Reset status to NEW
            delegation.assigned_user = None # Clear assignment so it can be re-delegated
            delegation.save()

            add_delegation_note(
                delegation_id, 
                request.user, 
                "ACTION: Restored task from Recycle Bin to Main Inbox queue."
            )
            messages.success(request, "Email successfully restored to the Live Inbox.")
            # Redirect back to recycle bin after restoration
            return redirect('outlook_recycle_bin')

        # --- 2. HANDLE METADATA UPDATES ---
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

        # --- 3. HANDLE NOTE SUBMISSION (Manual internal notes) ---
        elif 'note_content' in request.POST:
            note_content = request.POST.get('note_content')
            success, message = add_delegation_note(delegation_id, request.user, note_content)
            if success: 
                messages.success(request, "Internal note saved.")
            else:
                messages.error(request, message)
            return redirect('outlook_delegated_action', delegation_id=delegation_id)
        
        # --- 4. HANDLE REPLY/SEND EMAIL (Graph API Integration) ---
        elif 'reply_recipient' in request.POST:
            recipient = request.POST.get('reply_recipient')
            subject = request.POST.get('reply_subject')
            body_html = request.POST.get('reply_body')
            action_destination = request.POST.get('action_notes', 'EMAIL_REPLY')
            
            response = OutlookGraphService.send_outlook_email(target_email, recipient, subject, body_html)
            
            if response.get('success'):
                # Log the transaction in the history table
                log_delegation_transaction(
                    delegation_id, request.user, subject, recipient, 
                    action_type=action_destination
                )
                messages.success(request, f"Reply sent successfully and logged as {action_destination}.")
            else:
                messages.error(request, f"Failed to send email: {response.get('error')}")
                
            return redirect('outlook_delegated_action', delegation_id=delegation_id)

    # --- GET DATA FOR DISPLAY ---
    # Fetch original message content from Microsoft Graph API
    endpoint = f"messages/{delegation.email_id}"
    email_data = OutlookGraphService._make_graph_request(endpoint, target_email, method='GET')
    
    # Handle API errors gracefully
    if 'error' in email_data:
        messages.warning(request, "Could not fetch live email content. Showing local snippet instead.")
        email_display = {'subject': delegation.email_id, 'body': {'content': 'Live content unavailable.'}}
    else:
        email_display = email_data

    context = {
        'delegation': delegation,
        'email': email_display,
        'notes': delegation.notes.all().order_by('-created_at'),
        'target_email': target_email,
        'is_manager': is_manager,
    }
    return render(request, 'unity_internal_app/outlook_delegated_action.html', context)

@login_required
def outlook_delegate_to(request, email_id):
    """
    Handles the detailed delegation form for classification before assignment.
    UPDATED: Now handles 'Work Related: No' by moving tasks to the Recycle Bin 
    without requiring an agent selection.
    """
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    available_users = User.objects.filter(is_active=True).exclude(pk=request.user.pk)
    
    if request.method == 'POST':
        work_related = request.POST.get('work_related')
        assignee_pk = request.POST.get('agent_name')
        
        # 1. Capture ALL classification fields
        data_for_delegation = {
            'company_code': request.POST.get('company_code'),
            'email_category': request.POST.get('email_category'),
            'work_related': work_related,
            'comm_type': request.POST.get('comm_type') or 'Email',
        }

        # --- BRANCH A: NOT WORK RELATED (Recycle Bin) ---
        if work_related == 'No':
            # We create/update the delegation record with work_related=False
            # and status='COM' (Completed/Archived)
            from .models import EmailDelegation
            task, created = EmailDelegation.objects.update_or_create(
                email_id=email_id,
                defaults={
                    'work_related': False,
                    'status': 'COM',
                    'company_code': data_for_delegation['company_code'],
                    'email_category': data_for_delegation['email_category'],
                }
            )
            messages.error(request, "Email moved to Recycle Bin.")
            return redirect('outlook_dashboard')

        # --- BRANCH B: WORK RELATED (Delegation) ---
        else:
            if not assignee_pk or assignee_pk in ['', '__Select Agent__']:
                messages.error(request, "Please select an agent for delegation.")
            else:
                # Proceed with standard delegation logic
                data_for_delegation['status'] = 'DEL'
                success, message = delegate_email_task(
                    email_id, 
                    assignee_pk, 
                    request.user, 
                    classification_data=data_for_delegation
                )
                
                if success:
                    # 🚀 SEND REPLY THROUGH GRAPH API 🚀
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
                            messages.success(request, f"Task delegated and confirmation email sent to sender!")
                        else:
                            messages.warning(request, "Task delegated locally, but failed to send the Graph API reply.")
                    
                    except Exception as e:
                        messages.warning(request, f"Delegation saved, but email notification failed: {str(e)}")

                    return redirect('outlook_dashboard')
                else:
                    messages.error(request, message)

    # --- Fetch Data for GET Request ---
    endpoint = f"messages/{email_id}" 
    email_data = OutlookGraphService._make_graph_request(endpoint, target_email, method='GET') 

    if 'error' in email_data:
        messages.error(request, f"Error fetching email content: {email_data.get('error')}")
        return redirect('outlook_dashboard')

    raw_content = email_data.get('body', {}).get('content', '')
    received_date_str = email_data.get('receivedDateTime')
    
    # Ensure the delegation record exists/saved with date
    get_or_create_delegation_status(email_id, received_date_str=received_date_str)
    
    context = {
        'email_id': email_id,
        'email_subject': email_data.get('subject', '(No Subject)'),
        'email_content': raw_content, 
        'attachments': email_data.get('attachments', []),
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
    """Displays all Unity Internal emails marked as non-work related (Recycled)."""
    # FIX: Changed order_of to order_by
    recycled_tasks = EmailDelegation.objects.filter(work_related=False).order_by('-received_at')
    return render(request, 'unity_internal_app/recycle_bin.html', {'recycled_tasks': recycled_tasks})

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
    """Permanently deletes selected items from the database."""
    if request.method == 'POST':
        email_ids = request.POST.getlist('email_ids')
        EmailDelegation.objects.filter(email_id__in=email_ids).delete()
        messages.error(request, f"Permanently deleted {len(email_ids)} items.")
    return redirect('outlook_recycle_bin')