from urllib import response
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import pandas as pd
from .models import LevyData, ClientNotes, User
from django.utils import timezone
from django.db.models import Q
import csv
import io
from .models import AttorneySummary, Aod, Pfa, Lpi, LevyData
from .models import BankLine
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from decimal import Decimal,InvalidOperation
from .models import Org
from .models import LevyData, ClientNotes, BankLine, Org, TsrfPdfDocument 
from .forms import AddLevyForm, DocumentUploadForm 
from django.http import Http404, FileResponse, HttpRequest, HttpResponse, JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Max, Subquery, OuterRef, F
import os
from .models import OrgNotes
from .services.outlook_graph_service import fetch_inbox_messages, _make_graph_request
from .models import EmailDelegation, DelegationNote, EmailTransaction
from dateutil import parser
from django.conf import settings
from datetime import datetime

from .services import outlook_graph_service
# The original 'logger' import was removed to avoid AttributeError
# import logging 

# Define the list of reconciled Type values for exclusion
RECONCILED_TYPES = [
    'UKN', 
    'Contr&LPI', 
    'Unidentified', 
    'Risk/SMP', 
    'SMP', 
    'Refund', 
    'Contribution'
]

# --------------------------------------------------------------------- #
# AUTHENTICATION VIEWS (UNCHANGED)
# --------------------------------------------------------------------- #

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

# --------------------------------------------------------------------- #
# LEVY AND DATA MANAGEMENT VIEWS (UNCHANGED)
# --------------------------------------------------------------------- #

@login_required
def levy_list(request):
    search_query = request.GET.get('search_query', '').strip()
    
    current_filters = {
        'billing_period_filter': request.GET.get('billing_period_filter', ''), 
        'cbr_status_filter': request.GET.get('cbr_status_filter', ''),
    }

    # 1. Optimized Query: Get latest IDs using a single efficient values list
    latest_id_list = Org.objects.values('levy_number').annotate(
        latest_id=Max('id')
    ).values_list('latest_id', flat=True)

    # 2. Filter primary records
    # We remove the name-patching loop from here because it's the bottleneck
    levy_records_qs = Org.objects.filter(id__in=latest_id_list).only(
        'levy_number', 'employer_name', 'billing_period', 
        'cbr_status', 'overs_unders', 'due_amount', 'import_date'
    ).order_by('levy_number')

    # 3. Apply Filters
    if current_filters['billing_period_filter']:
        levy_records_qs = levy_records_qs.filter(billing_period__endswith=f"/{current_filters['billing_period_filter']}")
    if current_filters['cbr_status_filter']:
        levy_records_qs = levy_records_qs.filter(cbr_status=current_filters['cbr_status_filter'])
    if search_query:
        levy_records_qs = levy_records_qs.filter(
            Q(levy_number__icontains=search_query) | Q(employer_name__icontains=search_query)
        )

    # 4. PAGINATION: Only process 100 records at a time
    paginator = Paginator(levy_records_qs, 50) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 5. Patch names ONLY for the 100 records on the current page
    for record in page_obj:
        if not record.employer_name or record.employer_name.strip() == "":
            name_lookup = Org.objects.filter(levy_number=record.levy_number).exclude(
                Q(employer_name__isnull=True) | Q(employer_name="")
            ).order_by('-id').values_list('employer_name', flat=True).first()
            if name_lookup:
                record.employer_name = name_lookup

    # 6. Dropdown Options (Fast distinct queries)
    filter_options = {
        'billing_periods': sorted(list(set(Org.objects.values_list('billing_period', flat=True).exclude(billing_period=""))), reverse=True), 
        'cbr_statuses': Org.objects.values_list('cbr_status', flat=True).distinct().exclude(cbr_status__isnull=True),
    }

    context = {
        'levy_records': page_obj, # Pass the paginated object
        'search_query': search_query,
        'current_filters': current_filters, 
        'title': 'Employer Management Ledger'
    }
    context.update(filter_options)
    
    return render(request, 'TSRF_RECON_APP/levy_list.html', context)


@login_required
@transaction.atomic 
def levy_information(request, levy_number):
    """
    View to display and EDIT detailed information for a single levy record.
    Supports inline editing of the General Info and Directors tabs.
    """
    # 0. NORMALIZE: Ensure levy_number is 5 digits
    clean_levy_number = str(levy_number).strip().zfill(5)

    # 1. Fetch Master Profile record (Table: LevyData)
    levy_record = LevyData.objects.filter(levy_number=clean_levy_number).first()
    
    if not levy_record:
        levy_record = LevyData(levy_number=clean_levy_number, levy_name="New Record")

    # 2. Fetch Transactional Summary (Table: Org)
    org_summary = Org.objects.filter(levy_number=clean_levy_number).order_by('-id').first()

    # Name Patching logic
    if org_summary and (not org_summary.employer_name or org_summary.employer_name.strip() == ""):
        name_lookup = Org.objects.filter(levy_number=clean_levy_number).exclude(
            Q(employer_name__isnull=True) | Q(employer_name="")
        ).order_by('-id').values_list('employer_name', flat=True).first()
        if name_lookup:
            org_summary.employer_name = name_lookup
    
    pdf_upload_form = DocumentUploadForm()

    if request.method == 'POST':
        # --- Handle Inline Update from General / Directors Tab ---
        if 'update_general_info' in request.POST:
            try:
                # 1. Update General Info Fields
                levy_record.responsible_person = request.POST.get('responsible_person')
                levy_record.registration_number = request.POST.get('registration_number')
                levy_record.notice_email = request.POST.get('notice_email')
                levy_record.telephone = request.POST.get('telephone')
                levy_record.physical_address = request.POST.get('physical_address')
                levy_record.postal_address = request.POST.get('postal_address')
                levy_record.levy_user = request.POST.get('levy_user')
                levy_record.user_login = request.POST.get('user_login')
                levy_record.levy_user_2 = request.POST.get('levy_user_2')
                levy_record.user_login_2 = request.POST.get('user_login_2')

                # 2. Update Director 1 Fields
                levy_record.Director_Name_1 = request.POST.get('Director_Name_1')
                levy_record.Director_Mail_1 = request.POST.get('Director_Mail_1')
                levy_record.Director_Cell_1 = request.POST.get('Director_Cell_1')
                levy_record.Director_Address_1 = request.POST.get('Director_Address_1')

                # 3. Update Director 2 Fields
                levy_record.Director_Name_2 = request.POST.get('Director_Name_2')
                levy_record.Director_Mail_2 = request.POST.get('Director_Mail_2')
                levy_record.Director_Cell_2 = request.POST.get('Director_Cell_2')
                levy_record.Director_Address_2 = request.POST.get('Director_Address_2')

                # 4. Update Director 3 Fields
                levy_record.Director_Name_3 = request.POST.get('Director_Name_3')
                levy_record.Director_Mail_3 = request.POST.get('Director_Mail_3')
                levy_record.Director_Cell_3 = request.POST.get('Director_Cell_3')
                levy_record.Director_Address_3 = request.POST.get('Director_Address_3')

                # 5. Update Director 4 Fields
                levy_record.Director_Name_4 = request.POST.get('Director_Name_4')
                levy_record.Director_Mail_4 = request.POST.get('Director_Mail_4')
                levy_record.Director_Cell_4 = request.POST.get('Director_Cell_4')
                levy_record.Director_Address_4 = request.POST.get('Director_Address_4')
                
                # Save to database
                levy_record.save()
                messages.success(request, f'Master Profile and Director info for {clean_levy_number} updated!')
            except Exception as e:
                messages.error(request, f"Error saving profile: {e}")
            
            return redirect(f"{request.path}#general-info")

        # --- Handle PDF Uploads ---
        elif 'upload_document' in request.POST:
            pdf_upload_form = DocumentUploadForm(request.POST, request.FILES)
            if pdf_upload_form.is_valid():
                try:
                    document = pdf_upload_form.save(commit=False)
                    document.related_levy_number = clean_levy_number
                    document.uploaded_by = request.user.username
                    document.save() 
                    messages.success(request, 'Document uploaded successfully.')
                    return redirect(f"{request.path}#pdf-documents")
                except Exception as e:
                    messages.error(request, f"Error saving document: {e}")

        # --- Handle Org Notes Submission ---
        elif 'notes_text' in request.POST:
            note_text = request.POST.get('notes_text')
            if note_text:
                OrgNotes.objects.create(
                    Levy_number=clean_levy_number,
                    Date=datetime.now(), 
                    User=request.user.username,
                    Notes=note_text,
                )
                messages.success(request, 'Note added successfully!')
            return redirect(f"{request.path}#overview")

    # 3. GET Requests & Context Setup
    context = {
        'levy_record': levy_record,
        'org_summary': org_summary,
        'notes': ClientNotes.objects.filter(levy_number=clean_levy_number).order_by('-date'),
        'bank_lines': BankLine.objects.filter(Levy_number=clean_levy_number).order_by('-Date'),
        'pdf_upload_form': pdf_upload_form,
        'documents': TsrfPdfDocument.objects.filter(related_levy_number=clean_levy_number).order_by('-uploaded_at'),
        'org_notes': OrgNotes.objects.filter(Levy_number=clean_levy_number).order_by('-Date'),
        'latest_org_note': OrgNotes.objects.filter(Levy_number=clean_levy_number).order_by('-Date').first(),
        'email_logs': EmailDelegation.objects.filter(company_code__icontains=clean_levy_number).order_by('-received_at'),
    }
    return render(request, 'TSRF_RECON_APP/levy_information.html', context)
import json # Ensure this is at the top

@transaction.atomic
def import_data(request):
    """
    Handles CSV file upload and provides a summary pop-up with a downloadable report.
    Condition: Auto-reconcile ONLY if Reference contains 'CB' AND Recon column is 'Yes'.
    """
    context = {}

    if request.method == 'POST':
        if 'import_file' in request.FILES:
            csv_file = request.FILES['import_file']
            
            if not csv_file.name.endswith('.csv'):
                context['error_message'] = 'Invalid file type. Please upload a CSV file.'
                return render(request, 'TSRF_RECON_APP/Import.html', context)
            
            has_header = request.POST.get('header_row') is not None
            
            try:
                uploaded_file = csv_file.read().decode('latin-1')
                io_string = io.StringIO(uploaded_file)
                reader = csv.reader(io_string)
            except Exception as e:
                context['error_message'] = f"File reading error: {e}"
                return render(request, 'TSRF_RECON_APP/Import.html', context)
            
            if has_header:
                next(reader, None) 

            records_to_create = []
            import_report_data = [] # List to store data for the downloadable CSV
            auto_reconciled_count = 0
            manual_action_count = 0
            
            try:
                EXPECTED_COLUMNS = 9 
                line_count = 0

                for row in reader:
                    line_count += 1
                    if not any(row) or len(row) < EXPECTED_COLUMNS:
                        continue
                        
                    try:
                        # --- Data Cleansing and Conversion ---
                        transaction_date = datetime.strptime(row[0].strip(), '%d/%m/%Y').date()
                        amount_value = Decimal(row[1].strip().replace(',', ''))
                        other_ref = row[3].strip()
                        recon_csv_value = row[4].strip().lower() 

                        # --- LOGIC TRIGGER ---
                        if other_ref and 'CB' in other_ref.upper() and recon_csv_value == 'yes':
                            recon_status = 'Reconciled'
                            category = "Auto-Reconciled"
                            auto_reconciled_count += 1
                        else:
                            recon_status = 'Unreconciled'
                            category = "Manual Action Required"
                            manual_action_count += 1

                        # Store information for the summary report
                        import_report_data.append({
                            'Date': row[0].strip(),
                            'Ref': other_ref,
                            'Amount': row[1].strip(),
                            'Status': recon_status,
                            'Category': category
                        })

                        record = BankLine(
                            Date=transaction_date,
                            Amount=amount_value,
                            Reference_Description=row[2].strip(),
                            Other_Reference=other_ref or None, 
                            Recon=recon_status,
                            Levy_number=row[5].strip() or None,
                            Fisical=row[6].strip() or None,
                            Type=row[7].strip(),
                            Column_5=row[8].strip() or None,
                        )
                        records_to_create.append(record)
                        
                    except ValueError as ve:
                        continue
                        
                if records_to_create:
                    BankLine.objects.bulk_create(records_to_create)
                
                # --- Prepare Context for Pop-up ---
                context['show_summary'] = True
                context['auto_count'] = auto_reconciled_count
                context['manual_count'] = manual_action_count
                context['total_count'] = len(records_to_create)
                # Convert list to JSON string for Javascript
                context['report_json'] = json.dumps(import_report_data)

            except Exception as e:
                context['error_message'] = f"Unexpected error: {e}"
        else:
            context['error_message'] = 'No file was submitted.'
            
    return render(request, 'TSRF_RECON_APP/Import.html', context)


# --------------------------------------------------------------------- #
# BANKLINE VIEWS (REFRACTORED)
# --------------------------------------------------------------------- #

# Define the list of reconciled Type values for exclusion
RECONCILED_TYPES = [
    'UKN', 
    'Contr&LPI', 
    'Unidentified', 
    'Risk/SMP', 
    'SMP', 
    'Refund', 
    'Contribution'
]

def get_bank_line_queryset(allocated=False, search_query=''):
    """Helper function to filter bank lines based on allocation status."""
    
    if allocated:
        # Allocated: Levy_number is NOT NULL AND Levy_number is NOT ''
        queryset = BankLine.objects.filter(
            Q(Levy_number__isnull=False) & ~Q(Levy_number='')
        ).order_by('-Date')
        
        # *** NEW EXCLUSION LOGIC ***
        # Exclude lines where the 'Type' is one of the reconciled values
        queryset = queryset.exclude(Type__in=RECONCILED_TYPES)
        
    else:
        # Unallocated: Levy_number is NULL OR Levy_number is ''
        queryset = BankLine.objects.filter(
            Q(Levy_number__isnull=True) | Q(Levy_number='')
        ).order_by('-Date')
    
    if search_query:
        queryset = queryset.filter(
            Q(Levy_number__icontains=search_query) |
            Q(Reference_Description__icontains=search_query)
        )
    return queryset


@login_required
@transaction.atomic
def import_org_data(request):
    """
    Handles the file upload for ORG data, processes the CSV, and saves it to the Org table.
    """
    context = {}

    if request.method == 'POST':
        if 'org_import_file' in request.FILES:
            uploaded_file = request.FILES['org_import_file']
            has_header = request.POST.get('header_row') == 'on' 

            # 1. Get the current date and timestamp ONCE at the start of the import
            current_datetime = datetime.datetime.now()
            current_date = current_datetime.date()
            
            raw_data = uploaded_file.read()
            file_data = None
            
            # Handle Decoding
            try:
                file_data = raw_data.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    file_data = raw_data.decode('latin-1')
                    print("Warning: CSV file decoded using latin-1 encoding.")
                except Exception:
                    context['error_message'] = "Error: Could not decode the file. Ensure it is saved as UTF-8 or a standard Western encoding (Latin-1)."
                    return render(request, 'TSRF_RECON_APP/Import_Org.html', context)
            
            csv_reader = csv.reader(io.StringIO(file_data))
            
            if has_header:
                try:
                    next(csv_reader, None)
                except StopIteration:
                    context['error_message'] = "File is empty or contains only a header."
                    return render(request, 'TSRF_RECON_APP/Import_Org.html', context)
            
            org_objects = []
            line_count = 0
            EXPECTED_COLUMNS = 12
            
            try:
                for row in csv_reader:
                    line_count += 1
                    
                    if not any(row):
                        continue
                        
                    if len(row) < EXPECTED_COLUMNS: 
                        print(f"Skipping row {line_count} due to insufficient columns ({len(row)} of {EXPECTED_COLUMNS} expected): {row}")
                        continue
                    
                    # --- Data Conversion and Mapping ---
                    org_objects.append(Org(
                        # Data from CSV
                        levy_number=row[0].strip().replace("'", ""),
                        # employer_name=row[1].strip(),  <-- Excluded as requested
                        billing_period=row[2].strip(),
                        cbr_status=row[10].strip() or None,
                        
                        # Financial Fields
                        member_arrear_total=Decimal(row[3].strip().replace(',', '') or '0.00'),
                        member_additional_voluntary_contribution_total=Decimal(row[4].strip().replace(',', '') or '0.00'),
                        member_total=Decimal(row[5].strip().replace(',', '') or '0.00'),
                        employer_arrear_total=Decimal(row[6].strip().replace(',', '') or '0.00'),
                        employer_additional_voluntary_contribution_total=Decimal(row[7].strip().replace(',', '') or '0.00'),
                        employer_total=Decimal(row[8].strip().replace(',', '') or '0.00'),
                        due_amount=Decimal(row[9].strip().replace(',', '') or '0.00'),
                        overs_unders=Decimal(row[11].strip().replace(',', '') or '0.00'),

                        # 2. Add the current date and datetime
                        import_date=current_date, 
                        created_at=current_datetime,
                    ))

                # Perform bulk insertion
                if org_objects:
                    Org.objects.bulk_create(org_objects)
                    context['success_message'] = f"Success! Successfully processed and saved {len(org_objects)} ORG records to the database."
                else:
                    context['error_message'] = "No valid data rows found to import."

            except (InvalidOperation, ValueError) as e:
                context['error_message'] = f"Data Processing Failed at line {line_count}. Check the financial columns for non-numeric data. Error: {e}"
                print(f"ORG Import Conversion Error at line {line_count}: {e}")
            except IntegrityError:
                context['error_message'] = "A database integrity error occurred during ORG import. Check for duplicate entries."
            except Exception as e:
                context['error_message'] = f"Data Processing Failed at line {line_count}. General Error: {e}"
                print(f"ORG Import General Error at line {line_count}: {e}")
                
        else:
            context['error_message'] = "No file was selected for upload."

    return render(request, 'TSRF_RECON_APP/Import_Org.html', context)


@login_required
def org_table_view(request):
    """
    Fetches ONLY the records from the Org table that belong to the 
    MOST RECENT import date/time, then applies search/filter logic and pagination.
    """
    # 1. Retrieve all Filter and Search Values
    search_query = request.GET.get('search_query', '').strip()
    due_filter = request.GET.get('due_filter', '')
    cbr_filter = request.GET.get('cbr_filter', '')
    # REMOVED: agent_filter = request.GET.get('agent_filter', '')
    
    # 2. Determine the LATEST IMPORT DATE/TIME
    latest_import_data = Org.objects.aggregate(Max('created_at'))
    latest_datetime = latest_import_data.get('created_at__max')
    
    org_data = Org.objects.none() # Start with an empty queryset
    latest_period = None
    
    if latest_datetime:
        try:
            # Filter the queryset to only include the latest import batch
            org_data = Org.objects.filter(created_at=latest_datetime)
            
            latest_period = org_data.first().billing_period if org_data.exists() else None

            # 3. Apply all Filters (including the wildcard search)
            
            # --- Wildcard Search (Levy Number or Employer Name) ---
            if search_query:
                org_data = org_data.filter(
                    Q(levy_number__icontains=search_query) |
                    Q(employer_name__icontains=search_query)
                )

            # --- Due Amount Filter ---
            if due_filter == 'positive':
                org_data = org_data.filter(due_amount__gt=0)
            elif due_filter == 'negative':
                org_data = org_data.filter(due_amount__lt=0)
            elif due_filter == 'zero':
                org_data = org_data.filter(due_amount=0)

            # --- CBR Status Filter ---
            if cbr_filter:
                org_data = org_data.filter(cbr_status__iexact=cbr_filter)
            
            # --- Agent Filter (REMOVED: The 'agent' field does not exist on Org model) ---
            # if agent_filter:
            #     org_data = org_data.filter(agent__iexact=agent_filter)

            # Order the data
            org_data = org_data.order_by('levy_number', 'id') 

        except Exception as e:
            # Handle potential database errors gracefully
            org_data = Org.objects.none() 
            latest_period = None
            print(f"Error fetching filtered ORG data: {e}") 
            
    # 4. Get Unique Filter Choices for Dropdowns (Should fetch from ALL data, or at least the latest batch)
    
    # Fetch unique choices from the current *unfiltered* latest batch for dropdown options
    # If the latest_datetime is not None, use the base latest batch for choices
    base_org_data = Org.objects.filter(created_at=latest_datetime) if latest_datetime else Org.objects.none()

    cbr_statuses = base_org_data.values_list('cbr_status', flat=True).distinct().exclude(cbr_status__isnull=True).order_by('cbr_status')
    
    # REMOVED: agents = base_org_data.values_list('agent', flat=True).distinct().exclude(agent__isnull=True).order_by('agent')
    agents = [] # Provide an empty list to prevent errors in the template


    # 5. Set up Pagination
    paginator = Paginator(org_data, 24) # Show 24 records per page
    
    # Get the current page number from the URL, default to 1
    page_number = request.GET.get('page', 1)
    
    try:
        # 6. Get the Page object
        org_data_page = paginator.page(page_number)
    except PageNotAnInteger:
        org_data_page = paginator.page(1)
    except EmptyPage:
        org_data_page = paginator.page(paginator.num_pages)

    context = {
        'org_data_page': org_data_page, 
        'search_query': search_query,
        'due_filter': due_filter,
        'cbr_filter': cbr_filter,
        # REMOVED: 'agent_filter': agent_filter,
        'cbr_statuses': cbr_statuses, 
        'agents': agents, # Passed as empty list
        'latest_period': latest_period,
        'column_names': [
            'ID', 'Employer Code', 'Employer Name', 'Billing Period', 
            'Member Arrear Total', 'Member Add. Vol. Contrib. Total', 'Member Total',
            'Employer Arrear Total', 'Employer Add. Vol. Contrib. Total', 'Employer Total',
            'Due Amount', 'CBR Status', 'Overs/Unders', 'Import Date', 'Created At'
        ]
    }
    return render(request, 'TSRF_RECON_APP/Org_Table.html', context)

@login_required
def add_levy_view(request):
    """
    Handles both adding a new Levy and editing an existing one 
    in the external 'levy data' table.
    """
    # 1. Check if we are in 'Edit Mode'
    edit_id = request.GET.get('edit_id')
    instance = None
    
    if edit_id:
        # Fetch the existing record to populate the form
        instance = get_object_or_404(LevyData, levy_number=edit_id)

    if request.method == 'POST':
        # 2. Pass the instance to the form so it updates instead of creating a duplicate
        form = AddLevyForm(request.POST, instance=instance)
        
        if form.is_valid():
            try:
                saved_levy = form.save()
                if edit_id:
                    messages.success(request, f"Levy '{saved_levy.levy_name}' updated successfully!")
                    # Redirect back to the info page if we were editing
                    return redirect('levy_information', levy_number=saved_levy.levy_number)
                else:
                    messages.success(request, f"New levy '{saved_levy.levy_name}' added successfully!")
                    return redirect('levy_list')
                    
            except IntegrityError:
                messages.error(request, "Error: A levy with that number already exists. Please use a unique Levy Number.")
            except Exception as e:
                messages.error(request, f"Error saving levy: {e}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        # 3. For GET requests, if instance exists, the form will be pre-filled
        form = AddLevyForm(instance=instance)

    context = {
        'form': form,
        'is_edit': bool(edit_id),
        'levy_number': edit_id
    }
    return render(request, 'TSRF_RECON_APP/add_levy.html', context)

@login_required
def bankline_allocation(request, bank_line_id):
    """
    Handles updating the Levy Number and adding a Note (Column_6) 
    for a specific BankLine object.
    """
    # 1. Fetch the BankLine object
    bank_line = get_object_or_404(BankLine, pk=bank_line_id)

    if request.method == 'POST':
        # 2. Handle the Levy Number and Column_6 updates from the form
        new_levy_number = request.POST.get('Levy_number')
        new_column_6 = request.POST.get('Column_6')  # <-- Capture Column_6

        # Check if Levy_number OR Column_6 has changed (ignore Column_5/other fields)
        if bank_line.Levy_number != new_levy_number or bank_line.Column_6 != new_column_6:
            
            # 3. Update ONLY the allowed fields
            bank_line.Levy_number = new_levy_number
            bank_line.Column_6 = new_column_6  # <-- Set Column_6
            
            try:
                # 4. Save the changes to the database
                bank_line.save()
                messages.success(request, f"Levy Number updated to: {new_levy_number or 'Unassigned'}. Notes (Column 6) saved.")
            except Exception as e:
                # 5. Handle any database save errors
                messages.error(request, f"Error updating Bank Line: {e}")
        else:
            messages.info(request, "No changes were detected or saved.")

        # 6. Redirect back to the same page (GET request)
        return redirect('bankline_allocation', bank_line_id=bank_line.id)

    # 7. Handle the initial GET request (display the page)
    context = {
        'bank_line': bank_line,
    }
    
    return render(request, 'TSRF_RECON_APP/bankline_allocation.html', context)


from datetime import datetime
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def bankline_edits_view(request, levy_number):
    """
    Handles displaying and saving edits for a specific BankLine entry.
    Appends new notes to the history log in Column_6 with timestamp/user.
    """
    line_id = request.GET.get('line_id')
    bank_line_entry = None
    
    if line_id:
        try:
            bank_line_entry = BankLine.objects.get(id=line_id)
        except (BankLine.DoesNotExist, ValueError):
            bank_line_entry = None

    if request.method == 'POST' and bank_line_entry:
        # 1. Capture form data
        new_recon_status = request.POST.get('recon_status')
        new_note_text = request.POST.get('new_note', '').strip()
        
        bank_line_entry.Levy_number = request.POST.get('levy_number')
        bank_line_entry.Recon = new_recon_status
        bank_line_entry.Type = request.POST.get('type') 
        bank_line_entry.Fisical = request.POST.get('fisical_year')
        bank_line_entry.Column_5 = request.POST.get('note_selection')
        
        # 2. Append to History (Column_6) if a new note was typed
        if new_note_text:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            user = request.user.username # Captures the logged-in administrator
            formatted_note = f"[{timestamp} - {user}]: {new_note_text}"
            
            if bank_line_entry.Column_6:
                # Add new note to the TOP of the history log
                bank_line_entry.Column_6 = f"{formatted_note}\n\n{bank_line_entry.Column_6}"
            else:
                bank_line_entry.Column_6 = formatted_note
        
        try:
            bank_line_entry.save()
            messages.success(request, f"Bank Line #{bank_line_entry.id} updated successfully!")
            # Always return to the action list after save
            return redirect('unreconciled_banklines') 
            
        except Exception as e:
            messages.error(request, f"Error saving Bank Line #{bank_line_entry.id}: {e}")
            return redirect(f"{request.path}?line_id={bank_line_entry.id}")

    context = {
        'title': f'Bankline Edits for Levy {levy_number}',
        'levy_number': levy_number,
        'bank_line_entry': bank_line_entry,
    }
    return render(request, 'TSRF_RECON_APP/bankline_edits.html', context)

@login_required
def org_table_info(request, levy_number):
    """
    Displays detail for a single Org record (the latest one) and handles 
    the submission of new OrgNotes for that levy number.
    """
    latest_import_data = Org.objects.aggregate(max_created=Max('created_at'))
    latest_datetime = latest_import_data.get('max_created')

    if not latest_datetime:
        messages.error(request, "No import data found for ORG records.")
        return redirect('org_table_view')

    org_record = Org.objects.filter(
        levy_number=levy_number, 
        created_at=latest_datetime
    ).order_by('-id').first()

    if not org_record:
        org_record = Org.objects.filter(levy_number=levy_number).order_by('-created_at', '-id').first()

    if not org_record:
        raise Http404(f"ORG Record not found for Levy {levy_number}.")

    org_notes = OrgNotes.objects.filter(Levy_number=levy_number).order_by('-Date')
    
    if request.method == 'POST':
        note_text = request.POST.get('notes_text')
        
        if note_text:
            try:
                fiscal_date_str = org_record.billing_period
                date_obj = None
                if fiscal_date_str:
                    try:
                        # FIXED: changed datetime.datetime.strptime to datetime.strptime
                        date_obj = datetime.strptime(fiscal_date_str, '%d/%m/%Y').date()
                    except ValueError:
                        pass
                
                # FIXED: Use datetime.now() instead of datetime.datetime.now()
                OrgNotes.objects.create(
                    Levy_number=levy_number,
                    Date=datetime.now(), 
                    User=request.user.username,
                    Fiscal_date=date_obj,
                    Notes=note_text,
                )
                
                messages.success(request, "Note successfully added.")
                return redirect('org_table_info', levy_number=levy_number)

            except Exception as e:
                messages.error(request, f"Error saving note: {e}")
        else:
            messages.error(request, "Note text cannot be empty.")
            
    context = {
        'org_record': org_record,
        'org_notes': org_notes,
    }
    return render(request, 'TSRF_RECON_APP/org_table_info.html', context)

@login_required
def outlook_dashboard_view(request):
    """
    Displays the Shared Inbox for TSRF Recon.
    Filters out emails moved to the Recycle Bin (work_related=False).
    Access is now open to all authenticated users.
    """
    # 🟢 User permissions check removed from here

    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    inbox_data = fetch_inbox_messages(target_email, 25) 
    
    context = {'target_email': target_email, 'messages': []}
    
    if 'error' not in inbox_data:
        emails = inbox_data.get('value', [])
        email_ids = [e['id'] for e in emails]
        
        # 1. Fetch existing delegations for these emails
        delegations = {d.email_id: d for d in EmailDelegation.objects.filter(email_id__in=email_ids)}
        
        visible_emails = []
        
        for email in emails:
            e_id = email['id']
            delegation = delegations.get(e_id)
            
            # 2. If no record exists, auto-create a 'NEW' record
            if not delegation:
                delegation = EmailDelegation.objects.create(
                    email_id=e_id,
                    status='NEW',
                    work_related=True,  # Default to true for new items
                    received_at=parser.isoparse(email.get('receivedDateTime'))
                )
            
            # 3. FILTER LOGIC: Skip this email if it is marked as NOT work-related
            if not delegation.work_related:
                continue

            # 4. Populate display data for visible items
            email['delegation_status'] = delegation.get_status_display()
            email['assigned_to'] = delegation.assigned_user.username if delegation.assigned_user else "Unassigned"
            email['db_id'] = delegation.pk
            
            # Format date for template
            email['receivedDateTime'] = parser.isoparse(email.get('receivedDateTime'))
            
            visible_emails.append(email)
            
        context['messages'] = visible_emails
    else:
        messages.error(request, f"Graph API Error: {inbox_data['error']}")

    return render(request, 'TSRF_RECON_APP/outlook_dashboard.html', context)

from .services.outlook_graph_service import fetch_inbox_messages, send_outlook_email, _make_graph_request
from .services.delegation_service import (
    get_or_create_delegation_status, 
    delegate_email_task, 
    add_delegation_note, 
    get_delegated_emails_for_user,
    log_delegation_transaction
)

@login_required
def outlook_delegate_to(request, email_id):
    """
    TSRF Recon View: Detailed delegation form for classifying emails before assignment.
    """
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    
    # FETCH ALL ACTIVE USERS (Excluding the current delegator)
    available_users = User.objects.filter(is_active=True).exclude(pk=request.user.pk)
    
    if request.method == 'POST':
        work_related_status = request.POST.get('work_related') # 'Yes' or 'No'
        assignee_pk = request.POST.get('agent_name')
        
        # Capture classification fields from your updated HTML
        data_for_delegation = {
            'company_code': request.POST.get('company_code'),
            'email_category': request.POST.get('email_category'),
            'work_related': True if work_related_status == 'Yes' else False,
            'comm_type': request.POST.get('comm_type'),
        }
        
        # --- BRANCH A: NOT WORK RELATED (Move to Recycle Bin) ---
        if work_related_status == 'No':
            from .models import EmailDelegation
            # We use status 'REC' so it doesn't show up as 'Completed' in the main inbox
            EmailDelegation.objects.update_or_create(
                email_id=email_id,
                defaults={
                    'work_related': False,
                    'status': 'DLT', 
                    'company_code': data_for_delegation['company_code'],
                    'email_category': data_for_delegation['email_category'],
                }
            )
            messages.success(request, "Email moved to Recycle Bin.")
            return redirect('outlook_dashboard')

        # --- BRANCH B: WORK RELATED (Delegate to Agent) ---
        if assignee_pk:
            success, message = delegate_email_task(
                email_id, 
                assignee_pk, 
                request.user, 
                classification_data=data_for_delegation
            )
            
            if success:
                messages.success(request, f"Task successfully delegated! {message}")
                return redirect('outlook_dashboard')
            else:
                messages.error(request, message)
        else:
            messages.error(request, "Please select an agent for delegation.")

    # --- Fetch Data for GET Request ---
    endpoint = f"messages/{email_id}" 
    email_data = _make_graph_request(endpoint, target_email) 

    if 'error' in email_data:
        messages.error(request, f"Error fetching email content: {email_data.get('error')}")
        return redirect('outlook_dashboard')

    received_date_str = email_data.get('receivedDateTime')
    # Ensure a 'NEW' record exists in the DB so the dashboard shows the correct status
    get_or_create_delegation_status(email_id, received_date_str=received_date_str)
    
    context = {
        'email_id': email_id,
        'email_subject': email_data.get('subject', '(No Subject)'),
        'email_content': email_data.get('body', {}).get('content', ''), 
        'available_users': available_users,
        'attachments': email_data.get('attachments', []),
    }
    return render(request, 'TSRF_RECON_APP/outlook_delegate_to.html', context)


@login_required
def outlook_delegated_box(request):
    """
    TSRF Recon View: Displays emails delegated to the logged-in agent.
    """
    delegations = get_delegated_emails_for_user(request.user)
    tasks = []
    target_email = settings.OUTLOOK_EMAIL_ADDRESS 

    for delegation in delegations:
        endpoint = f"messages/{delegation.email_id}?$select=subject,from,receivedDateTime"
        email_data = _make_graph_request(endpoint, target_email)
        
        if 'error' not in email_data:
            tasks.append({
                'delegation_id': delegation.pk,
                'status': delegation.get_status_display(),
                'subject': email_data.get('subject'),
                'from': email_data.get('from', {}).get('emailAddress', {}).get('name', 'Unknown'),
                'received': email_data.get('receivedDateTime'),
                'category': delegation.email_category
            })

    return render(request, 'TSRF_RECON_APP/outlook_delegated_box.html', {'tasks': tasks})


@login_required
def outlook_delegated_action(request, delegation_id):
    """
    TSRF Recon View: Handles task management, email replies, 
    and restoration from the Recycle Bin (DLT/REC status).
    """
    delegation = get_object_or_404(EmailDelegation, pk=delegation_id)
    
    # PERMISSION CHECK: 
    is_admin = request.user.is_superuser or request.user.username.lower() == 'omega'
    if delegation.assigned_user != request.user and not is_admin:
        messages.error(request, "You do not have permission to view this task.")
        return redirect('outlook_delegated_box')

    target_email = settings.OUTLOOK_EMAIL_ADDRESS 

    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        # 1. HANDLE RESTORE (Status DLT/REC -> NEW)
        if action_type == 'restore_to_inbox':
            delegation.status = 'NEW'
            delegation.work_related = True
            delegation.assigned_user = None # Clear previous assignment
            delegation.save()

            add_delegation_note(
                delegation_id, 
                request.user, 
                "ACTION: Restored task from Recycle Bin to Live Inbox."
            )
            messages.success(request, "Email successfully restored to the Live Inbox.")
            return redirect('outlook_recycle_bin')

        # 2. HANDLE METADATA UPDATES
        elif action_type == 'update_metadata':
            delegation.company_code = request.POST.get('company_code')
            delegation.email_category = request.POST.get('email_category')
            new_status = request.POST.get('status')
            
            delegation.status = new_status
            # Sync work_related boolean based on status selection
            if new_status in ['DLT', 'REC']:
                delegation.work_related = False
            else:
                delegation.work_related = True
            
            delegation.save()
            messages.success(request, "Task metadata updated successfully.")
            return redirect('outlook_delegated_action', delegation_id=delegation_id)

        # 3. HANDLE INTERNAL NOTE
        elif 'note_content' in request.POST:
            note_content = request.POST.get('note_content')
            success, message = add_delegation_note(delegation_id, request.user, note_content)
            if success: messages.success(request, message)
            else: messages.error(request, message)
            return redirect('outlook_delegated_action', delegation_id=delegation_id)
        
        # 4. HANDLE EXTERNAL REPLY (Available if not in Recycle Bin)
        elif 'reply_recipient' in request.POST and delegation.status not in ['DLT', 'REC']:
            recipient = request.POST.get('reply_recipient')
            subject = request.POST.get('reply_subject')
            body = request.POST.get('reply_body')
            
            # Use the Class Method correctly
            result = outlook_graph_service.send_outlook_email(recipient, subject, body)
            
            if result.get('success'):
                log_delegation_transaction(delegation_id, request.user, subject, recipient)
                messages.success(request, "Reply sent successfully.")
            else:
                messages.error(request, f"Reply failed: {result.get('error')}")
            return redirect('outlook_delegated_action', delegation_id=delegation_id)

    # Fetch email content
    endpoint = f"messages/{delegation.email_id}"
    email_data = outlook_graph_service._make_graph_request(endpoint, target_email)
    
    context = {
        'delegation': delegation,
        'email': email_data if 'error' not in email_data else None,
        'notes': delegation.notes.all().order_by('-created_at'),
        'target_email': target_email,
    }
    return render(request, 'TSRF_RECON_APP/outlook_delegated_action.html', context)

@login_required
def outlook_email_content(request, email_id):
    """
    Helper View: Serves raw HTML for the iframe preview in TSRF_RECON.
    """
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    endpoint = f"messages/{email_id}" 
    email_data = _make_graph_request(endpoint, target_email)

    if 'error' in email_data:
        return HttpResponse("Error loading email.", status=500)

    content = email_data.get('body', {}).get('content', '')
    wrapped_content = f"<!DOCTYPE html><html><body>{content}</body></html>"
    return HttpResponse(wrapped_content, content_type='text/html')

@login_required
def send_email_view(request):
    """
    Handles displaying the email form and processing the email submission 
    to the Microsoft Graph API for the TSRF_RECON_APP.
    """
    target_email = settings.OUTLOOK_EMAIL_ADDRESS
    
    if request.method == 'POST':
        recipient = request.POST.get('recipient')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        
        if not all([recipient, subject, body]):
            messages.error(request, "All fields are required.")
            return render(request, 'TSRF_RECON_APP/send_email_form.html', {'target_email': target_email})
        
        # Call the service function
        result = send_outlook_email(target_email, recipient, subject, body)
        
        if result.get('success'):
            messages.success(request, f"Email sent successfully from {target_email} to {recipient}.")
            return redirect('outlook_dashboard')
        else:
            error_message = f"Email failed to send: {result.get('error', 'Unknown API Error')}"
            messages.error(request, error_message)
            return render(request, 'TSRF_RECON_APP/send_email_form.html', {
                'recipient': recipient,
                'subject': subject,
                'body': body,
                'target_email': target_email
            })

    return render(request, 'TSRF_RECON_APP/send_email_form.html', {'target_email': target_email})

@login_required
def outlook_recycle_bin(request):
    archived_tasks = EmailDelegation.objects.filter(work_related=False).order_by('-received_at')
    tasks = []
    target_email = settings.OUTLOOK_EMAIL_ADDRESS 

    for task in archived_tasks:
        endpoint = f"messages/{task.email_id}?$select=subject,from,receivedDateTime"
        email_data = _make_graph_request(endpoint, target_email)
        
        if 'error' not in email_data:
            tasks.append({
                'pk': task.pk,           # Add this to fix the URL error
                'db_id': task.pk,        # Keep this for your checkboxes
                'email_id': task.email_id,
                'subject': email_data.get('subject'),
                'from': email_data.get('from', {}).get('emailAddress', {}).get('name', 'Unknown'),
                'received_at': task.received_at, 
                'company_code': task.company_code,
                'email_category': task.email_category
            })

    return render(request, 'TSRF_RECON_APP/outlook_recycle_bin.html', {'recycled_tasks': tasks})

@login_required
def outlook_delete_permanent(request):
    """Permanently removes tasks from the database."""
    if request.method == 'POST':
        email_ids = request.POST.getlist('email_ids')
        if email_ids:
            # We filter by work_related=False to ensure only archived items are deleted
            deleted_count = EmailDelegation.objects.filter(email_id__in=email_ids, work_related=False).delete()
            messages.success(request, f"Permanently deleted {deleted_count[0]} items.")
        else:
            messages.warning(request, "No items selected.")
    return redirect('outlook_recycle_bin')

@login_required
def restore_from_recycle_bin(request, delegation_id):
    """Restores an archived email back to 'NEW' status so it can be re-delegated."""
    task = get_object_or_404(EmailDelegation, pk=delegation_id)
    task.work_related = True
    task.status = 'NEW'
    task.save()
    
    messages.success(request, "Email restored to live inbox successfully.")
    return redirect('outlook_dashboard')


import requests
from django.utils import timezone

@login_required
def outlook_compose(request):
    """
    Handles rendering the compose form and processing submission
    using the send_outlook_email service function.
    """
    # 1. Capture company_code from multiple possible sources to prevent empty values
    # Try POST first (form), then GET (URL), then check referring URL if needed
    company_code = request.POST.get('company_code') or request.GET.get('company_code', '')
    
    to_email = request.GET.get('to_email', '')
    # Ensure subject doesn't break if company_code is missing
    default_subject = request.GET.get('subject') or f"Query: Levy {company_code}".strip()
    target_sender = settings.OUTLOOK_EMAIL_ADDRESS

    if request.method == 'POST':
        recipient = request.POST.get('to_email')
        subject = request.POST.get('subject')
        
        # Capture content from the Rich Text editor
        body = request.POST.get('email_body_html_content') or request.POST.get('body')

        if not all([recipient, subject, body]):
            messages.error(request, "All fields are required. Please ensure the email body is not empty.")
        else:
            # 2. Call the service function to send via Microsoft Graph
            result = send_outlook_email(target_sender, recipient, subject, body)

            if result.get('success'):
                # 3. Create a UNIQUE Email ID to prevent IntegrityError (Duplicate Entry)
                # We append a timestamp to ensure the database unique constraint isn't violated
                timestamp_str = timezone.now().strftime('%Y%m%d-%H%M%S')
                unique_email_id = f"Sent: {subject[:40]} [{timestamp_str}]"

                EmailDelegation.objects.create(
                    company_code=company_code,
                    email_id=unique_email_id,
                    status='COM',
                    # Using 'notes' if your model allows it, otherwise use the appropriate field
                    # notes=body, 
                    email_category='Outgoing',
                    received_at=timezone.now() 
                )
                
                messages.success(request, f"Email sent successfully to {recipient}.")
                
                # 4. Redirect with a fallback to avoid NoReverseMatch
                if company_code:
                    return redirect('levy_information', levy_number=company_code)
                else:
                    messages.warning(request, "Email sent, but could not return to specific Levy page.")
                    return redirect('levy_list')
            else:
                messages.error(request, f"Email failed: {result.get('error')}")

    context = {
        'to_email': to_email,
        'company_code': company_code,
        'subject': default_subject,
        'target_email': target_sender
    }
    return render(request, 'TSRF_RECON_APP/compose_email.html', context)

@login_required
def outlook_delegated_action(request, pk):
    """View to handle clicking 'View Detail' on an email log."""
    log = get_object_or_404(EmailDelegation, pk=pk)
    
    context = {
        'log': log
    }
    return render(request, 'TSRF_RECON_APP/email_detail.html', context)


@login_required
def unreconciled_banklines(request):
    """
    Unified Action View: Reflects all unreconciled entries.
    Entries drop off once 'Recon' status is set to 'Reconciled'.
    """
    # 1. Capture Filters and Search
    search_query = request.GET.get('search_query', '').strip()
    note_filter = request.GET.get('note_filter', '').strip()
    deposit_date = request.GET.get('deposit_date', '').strip()
    type_filter = request.GET.get('type_filter', '').strip()

    # 2. Base Logic: Exclude anything marked as 'Reconciled'
    # This is the master trigger. Anything 'Unreconciled' or 'Review' stays here.
    queryset = BankLine.objects.exclude(Recon='Reconciled').order_by('-Date')

    # 3. Apply Multi-Parameter Filtering
    if search_query:
        queryset = queryset.filter(
            Q(Reference_Description__icontains=search_query) |
            Q(Levy_number__icontains=search_query)
        )
    if note_filter:
        queryset = queryset.filter(Column_5=note_filter)
    if deposit_date:
        queryset = queryset.filter(Date=deposit_date)
    if type_filter:
        queryset = queryset.filter(Type__icontains=type_filter)

    # 4. Pagination
    paginator = Paginator(queryset, 25)
    page_number = request.GET.get('page')
    bank_lines_page = paginator.get_page(page_number)

    context = {
        'bank_lines_page': bank_lines_page,
        'search_query': search_query,
        'note_filter': note_filter,
        'type_filter': type_filter,
        'deposit_date': deposit_date,
        'title': 'Unreconciled Banklines',
        'note_options': [
            "AOD CONRIBUTIONS", "AOD LPI", "DIFFERENCE TO FINALISED BILL AND PAYMENT", 
            "EMPLOYER TO FINALISE", "RECONSILED", "SYSTEM ISSUE"
        ]
    }
    return render(request, 'TSRF_RECON_APP/unreconciled_banklines.html', context)

@login_required
def global_bank_view(request):
    """
    Master Ledger with Status and Date filtering.
    """
    search_query = request.GET.get('search_query', '').strip()
    status_filter = request.GET.get('status_filter', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    queryset = BankLine.objects.all().order_by('-Date')

    # 1. Status Filter (Reconciled vs Unreconciled)
    if status_filter == 'Reconciled':
        queryset = queryset.filter(Recon='Reconciled')
    elif status_filter == 'Unreconciled':
        queryset = queryset.exclude(Recon='Reconciled')

    # 2. Date Range Filter (Transaction Date)
    if start_date and end_date:
        queryset = queryset.filter(Date__range=[start_date, end_date])

    # 3. Wildcard Search
    if search_query:
        queryset = queryset.filter(
            Q(Reference_Description__icontains=search_query) |
            Q(Levy_number__icontains=search_query)
        )

    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page')
    bank_lines_page = paginator.get_page(page_number)

    context = {
        'bank_lines_page': bank_lines_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'title': 'Global Bank Ledger'
    }
    return render(request, 'TSRF_RECON_APP/global_bank.html', context)

@login_required
def export_bank_csv(request):
    """
    Advanced Export: respects status and date filters from the UI.
    """
    status_filter = request.GET.get('status_filter', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    queryset = BankLine.objects.all().order_by('-Date')

    # Apply same filters as the view for consistent export
    if status_filter == 'Reconciled':
        queryset = queryset.filter(Recon='Reconciled')
    elif status_filter == 'Unreconciled':
        queryset = queryset.exclude(Recon='Reconciled')
    
    if start_date and end_date:
        queryset = queryset.filter(Date__range=[start_date, end_date])

    response = HttpResponse(content_type='text/csv')
    filename = f"Bank_Export_{status_filter if status_filter else 'All'}.csv"
    from django.utils import timezone
    response['Content-Disposition'] = f'attachment; filename="Billing_Summary_{timezone.now().date()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Recon Status', 'Date', 'Amount', 'Reference', 'Levy', 'Fiscal', 'Type', 'Note Selector', 'Admin Note'])

    for line in queryset:
        status = 'Reconciled' if line.Recon == 'Reconciled' else 'Unreconciled'
        writer.writerow([
            status, line.Date, line.Amount, line.Reference_Description,
            line.Levy_number, line.Fisical, line.Type, line.Column_5, line.Column_6
        ])

    return response

import numpy as np  # Add this import at the top

@login_required
def import_levy_data(request):
    """
    Standalone view to import/update the Master Levy Data table.
    Handles duplicates and converts NaN (empty cells) to None for DecimalFields.
    """
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        
        try:
            df = pd.read_excel(excel_file, dtype={
                'Levy_Number': str,
                'Responsible Person ID Number': str,
                'Director_Cell_1': str,
                'Director_Cell_2': str
            })

            # Helper to handle NaN/Empty values for Decimals and Dates
            def clean_val(val, is_decimal=False):
                if pd.isna(val) or str(val).lower() in ['nan', '', 'none', 'null']:
                    return 0 if is_decimal else None
                return val

            def parse_date(date_val):
                if pd.isna(date_val) or str(date_val).lower() in ['nan', '']:
                    return None
                try:
                    return pd.to_datetime(date_val).date()
                except:
                    return None

            with transaction.atomic():
                for index, row in df.iterrows():
                    levy_num = str(row.get('Levy_Number', '')).strip().zfill(5)
                    if not levy_num or levy_num == '00000':
                        continue

                    # --- DUPLICATE CLEANUP ---
                    existing_qs = LevyData.objects.filter(levy_number=levy_num)
                    
                    if existing_qs.exists():
                        # If more than one exists, keep the first, delete others
                        obj = existing_qs.first()
                        if existing_qs.count() > 1:
                            existing_qs.exclude(pk=obj.pk).delete()
                    else:
                        obj = LevyData(levy_number=levy_num)

                    # --- MAPPING WITH CLEANING ---
                    obj.levy_name = clean_val(row.get('Levy_Name'))
                    obj.mip_status = clean_val(row.get('MIP_Status'))
                    obj.commencement_date = parse_date(row.get('Commencement_Date'))
                    obj.termination_date = clean_val(row.get('Termination_Date'))
                    
                    # Contact Info
                    obj.responsible_person = clean_val(row.get('Responsible_Person'))
                    obj.responsible_person_id = clean_val(row.get('Responsible Person ID Number'))
                    obj.responsible_person_email = clean_val(row.get('Responsible Person Email Address'))
                    
                    # Financial Fields (Using is_decimal=True to avoid 'nan' error)
                    obj.due_amount_field = clean_val(row.get('Due Amount'), is_decimal=True)
                    obj.total_lpi_outstanding = clean_val(row.get('Total LPI Outstanding'), is_decimal=True)
                    obj.overs_unders_field = clean_val(row.get('Overs & Unders'), is_decimal=True)
                    obj.total_unallocated_deposits = clean_val(row.get('Total Unallocated Deposits'), is_decimal=True)
                    
                    # Status Fields
                    obj.cbr_status_field = clean_val(row.get('CBR Status'))
                    obj.administrator = clean_val(row.get('Administrator'))
                    obj.termination_reason = clean_val(row.get('Termination_Reason'))
                    obj.termination_status = clean_val(row.get('Termination_Status'))
                    
                    # Attorney/Director Info
                    obj.attorney_case = clean_val(row.get('Attorney_Case'))
                    obj.attorneys = clean_val(row.get('Attorneys'))
                    obj.director_name_1 = clean_val(row.get('Director_Name_1'))
                    
                    obj.save()

            messages.success(request, f"Import successful! Processed {len(df)} records.")
            return redirect('dashboard')

        except Exception as e:
            messages.error(request, f"Import Error: {str(e)}")
            
    return render(request, 'TSRF_RECON_APP/import_form.html')

from django.db.models import Max, Sum, Q

@login_required
def billing_summary(request):
    # 1. Get latest import IDs per Levy Number
    latest_ids = Org.objects.values('levy_number').annotate(latest_id=Max('id')).values_list('latest_id', flat=True)
    queryset = Org.objects.filter(id__in=latest_ids)

    # 2. Setup lookup for metadata (Name and MIP) from LevyData
    levy_master_info = {
        item.levy_number: {'name': item.levy_name, 'mip': item.mip_status}
        for item in LevyData.objects.all().only('levy_number', 'levy_name', 'mip_status')
    }

    # 3. Apply Filters (Search, Period, CBR)
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(levy_number__icontains=search_query) | 
            # Search by Name in the LevyData master lookup via levy_number
            Q(levy_number__in=LevyData.objects.filter(levy_name__icontains=search_query).values('levy_number'))
        )

    selected_periods = request.GET.getlist('period')
    if selected_periods:
        queryset = queryset.filter(billing_period__in=selected_periods)

    selected_cbr = request.GET.getlist('cbr')
    if selected_cbr:
        queryset = queryset.filter(cbr_status__in=selected_cbr)

    # 4. Final Data Assembly & MIP Filtering
    selected_mip = request.GET.getlist('mip')
    filtered_data = []
    for record in queryset:
        info = levy_master_info.get(record.levy_number, {})
        record.display_name = info.get('name', "Unknown")
        record.display_mip = info.get('mip', "N/A")
        
        if not selected_mip or record.display_mip in selected_mip:
            filtered_data.append(record)

# 5. Handle CSV Export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        # Use timezone.now().date() to avoid the 'method_descriptor' error
        filename_date = timezone.now().date()
        response['Content-Disposition'] = f'attachment; filename="Billing_Summary_{filename_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Levy Number', 'Employer Name', 'Billing Period', 'CBR Status', 'MIP Status', 'Due Amount'])
        
        for row in filtered_data:
            writer.writerow([
                row.levy_number, 
                row.display_name, 
                row.billing_period, 
                row.cbr_status, 
                row.display_mip, 
                row.due_amount
            ])
        return response

    # 6. Standard Render
    total_due = sum(r.due_amount for r in filtered_data)
    context = {
        'billing_data': filtered_data,
        'total_due': total_due,
        'billing_periods': Org.objects.filter(id__in=latest_ids).values_list('billing_period', flat=True).distinct(),
        'cbr_statuses': Org.objects.filter(id__in=latest_ids).values_list('cbr_status', flat=True).distinct(),
        'mip_statuses': LevyData.objects.values_list('mip_status', flat=True).distinct(),
        'selected_periods': selected_periods,
        'selected_cbr': selected_cbr,
        'selected_mip': selected_mip,
        'search_query': search_query,
    }
    return render(request, 'TSRF_RECON_APP/billing_summary.html', context)


from itertools import chain
from operator import attrgetter


def view_email_thread(request, delegation_id):
    # 1. Fetch the main delegation record
    delegation = get_object_or_404(EmailDelegation, id=delegation_id)
    
    # 2. Get internal notes and external transactions
    notes = DelegationNote.objects.filter(delegation=delegation)
    transactions = EmailTransaction.objects.filter(delegation=delegation)
    
    # 3. Combine into a timeline sorted by date
    # We unify the 'created_at' and 'sent_at' under a single sortable attribute
    timeline = sorted(
        chain(notes, transactions),
        key=lambda x: getattr(x, 'created_at', getattr(x, 'sent_at', None)),
        reverse=True
    )
    
    # 4. Fetch the email body from Microsoft Graph 
    # (Assuming you have a helper function 'get_email_body_from_graph')
    # email_content = get_email_body_from_graph(delegation.email_id)
    email_content = "This is the original email content fetched via Graph API using ID: " + delegation.email_id

    context = {
        'task': delegation,
        'email_body': email_content,
        'timeline': timeline,
    }
    return render(request, 'email_thread.html', context)

def attorney_list(request):
    """List view with filtering, search, pagination, and export."""
    
    # 1. Base Queryset
    records = AttorneySummary.objects.all().order_by('a_levy_number')

    # 2. Get Filter and Search Parameters
    f_aod = request.GET.get('aod')
    f_pfa = request.GET.get('pfa')
    f_mip = request.GET.get('mip')
    f_admin = request.GET.get('admin')
    f_search = request.GET.get('search') # For Levy or Levy Name

    # 3. Apply Filters
    if f_aod:
        records = records.filter(d_aod__icontains=f_aod)
    if f_pfa:
        records = records.filter(e_pfa__icontains=f_pfa)
    if f_mip:
        records = records.filter(f_mip_status__icontains=f_mip)
    if f_admin:
        records = records.filter(i_administrator__icontains=f_admin)
        
    # SEARCH LOGIC: Check Levy Number OR Levy Name
    if f_search:
        records = records.filter(
            Q(a_levy_number__icontains=f_search) | 
            Q(b_levy_name__icontains=f_search)
        )

    # 4. Handle Excel Export (Exports filtered/searched results)
    if 'export' in request.GET:
        return export_filtered_attorneys(records)

    # 5. Pagination (25 per page)
    paginator = Paginator(records, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Dropdown data
    admins = AttorneySummary.objects.values_list('i_administrator', flat=True).distinct()
    mip_statuses = AttorneySummary.objects.values_list('f_mip_status', flat=True).distinct()

    context = {
        'page_obj': page_obj,
        'admins': admins,
        'mip_statuses': mip_statuses,
    }
    return render(request, 'attorney_summary_detail.html', context)

def export_filtered_attorneys(queryset):
    """Exports the filtered attorney queryset to Excel."""
    data = list(queryset.values(
        'a_levy_number', 'b_levy_name', 'c_attorney', 'd_aod', 
        'e_pfa', 'f_mip_status', 'g_default_period', 'i_administrator'
    ))
    df = pd.DataFrame(data)
    
    # Rename columns for Excel
    df.columns = [
        'Levy Number', 'Levy Name', 'Attorney', 'AOD Status', 
        'PFA Status', 'MIP Status', 'Default Period', 'Administrator'
    ]

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Filtered_Attorney_Summary.xlsx'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Summary')
    
    return response

def attorney_case_view(request, levy_number):
    """Detailed view for a specific Attorney Case with sub-tables."""
    # Fetch core data
    levy = get_object_or_404(LevyData, levy_number=levy_number)
    attorney = get_object_or_404(AttorneySummary, a_levy_number=levy_number)
    
    # Fetch related records for the sub-tables
    aod_records = Aod.objects.filter(levy_number=levy_number)
    pfa_records = Pfa.objects.filter(levy_number=levy_number)
    
    # Fetch notes
    billing_notes = ClientNotes.objects.filter(levy_number=levy_number).order_by('-date')
    
    context = {
        'levy': levy,
        'attorney': attorney,
        'aod_records': aod_records,
        'pfa_records': pfa_records,
        'billing_notes': billing_notes,
    }
    return render(request, 'attorney_summary_detail.html', context)

def get_attorney_detail_ajax(request, levy_number):
    """AJAX endpoint to fetch specific case data and live Org financials."""
    # 1. Fetch Core Data
    attorney = get_object_or_404(AttorneySummary, a_levy_number=levy_number)
    levy_master = LevyData.objects.filter(levy_number=levy_number).first()
    
    # 2. Fetch LATEST financial data from Org table
    # We order by -import_date and -id to get the most recent record
    latest_org = Org.objects.filter(levy_number=levy_number).order_by('-import_date', '-id').first()

    # 3. Fetch Sub-table data
    aods = list(Aod.objects.filter(levy_number=levy_number).values(
        'aod_number', 'aod_amount', 'repay_amount', 'current_status'
    ))
    pfas = list(Pfa.objects.filter(levy_number=levy_number).values(
        'pfa_number', 'pfa_status', 'pfa_type', 'determination_due_date'
    ))
    notes = list(ClientNotes.objects.filter(levy_number=levy_number).order_by('-date').values(
        'date', 'notes_text', 'user'
    ))

    # 4. Construct Data Package
    data = {
        'levy_number': attorney.a_levy_number,
        'levy_name': attorney.b_levy_name,
        'attorney_name': attorney.c_attorney,
        'aod_status': attorney.d_aod,
        'pfa_status': attorney.e_pfa,
        'default_period': attorney.g_default_period,
        'admin': attorney.i_administrator,
        
        # Financials from Org Table
        'fiscal': latest_org.billing_period if latest_org else "N/A",
        'cbr': latest_org.cbr_status if latest_org else "T.M.P.",
        'due_amount': str(latest_org.due_amount) if latest_org else "0.00",
        'overs_unders': str(latest_org.overs_unders) if latest_org else "0.00",
        
        'aods': aods,
        'pfas': pfas,
        'notes': notes
    }
    return JsonResponse(data)

def aod_list(request):
    """AOD Master List with filtering, date range, pagination, and export."""
    
    # 1. Base Queryset
    records = Aod.objects.all().order_by('-aod_start_date')

    # 2. Get Filter Parameters
    f_search = request.GET.get('search')
    f_status = request.GET.get('status')
    f_start_date = request.GET.get('start_date')
    f_end_date = request.GET.get('end_date')

    # 3. Apply Filters
    if f_status:
        records = records.filter(aod_status__icontains=f_status)
    
    if f_search:
        # Search Levy Number or AOD Number
        records = records.filter(
            Q(levy_number__icontains=f_search) | 
            Q(aod_number__icontains=f_search)
        )

    # Date Range Filter on AOD Start Date
    if f_start_date and f_end_date:
        records = records.filter(aod_start_date__range=[f_start_date, f_end_date])

    # 4. Handle Export
    if 'export' in request.GET:
        return export_aod_list(records)

    # 5. Pagination (25 per page)
    paginator = Paginator(records, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Efficiently map Levy Names to the current page only
    levy_nums = [r.levy_number for r in page_obj]
    levy_names = {l.levy_number: l.levy_name for l in LevyData.objects.filter(levy_number__in=levy_nums)}
    
    for r in page_obj:
        r.levy_name = levy_names.get(r.levy_number, "Unknown")

    # Get unique statuses for dropdown
    statuses = Aod.objects.values_list('aod_status', flat=True).distinct()

    context = {
        'page_obj': page_obj,
        'statuses': statuses,
    }
    return render(request, 'aod_detail.html', context)

def export_aod_list(queryset):
    """Excel export for filtered AOD records."""
    # Create list of dicts for DataFrame
    levy_names = {l.levy_number: l.levy_name for l in LevyData.objects.all()}
    
    data = []
    for r in queryset:
        data.append({
            'Levy Number': r.levy_number,
            'Levy Name': levy_names.get(r.levy_number, "Unknown"),
            'AOD Amount': r.aod_amount,
            'AOD Number': r.aod_number,
            'AOD Status': r.aod_status,
            'Start Date': r.aod_start_date,
            'Repay Day': r.repayment_date.strftime('%d') if r.repayment_date else '20'
        })

    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=AOD_Export_{datetime.now().strftime("%Y%m%d")}.xlsx'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='AOD Master List')
    
    return response

def get_aod_detail_ajax(request, aod_number):
    """Fetches full AOD details and REAL installment schedule from Org table."""
    aod = get_object_or_404(Aod, aod_number=aod_number)
    levy = LevyData.objects.filter(levy_number=aod.levy_number).first()

    # Query the 'Org' table for real billing data linked to this levy
    # Filtering by levy_number to show the financial breakdown
    org_billing = Org.objects.filter(levy_number=aod.levy_number).order_by('-billing_period')

    installments = []
    for item in org_billing:
        # Calculating balance: Due Amount + Overs/Unders
        # Adjust this logic if you have a specific 'Paid' column in your DB
        balance = float(item.due_amount or 0) + float(item.overs_unders or 0)
        
        installments.append({
            'ref': item.billing_period, # Using Billing Period as the reference
            'fiscal': item.import_date.strftime('%d/%m/%Y') if item.import_date else 'N/A', 
            'amount': float(item.due_amount or 0), 
            'deposit': float(item.member_total or 0) + float(item.employer_total or 0), 
            'bal': balance, 
            'rec': "Yes" if balance <= 0 else "No"
        })

    data = {
        'aod_number': aod.aod_number,
        'levy_number': aod.levy_number,
        'levy_name': levy.levy_name if levy else "Unknown",
        'aod_type': "Contributions", 
        'start_date': aod.aod_start_date.strftime('%d/%m/%Y') if aod.aod_start_date else 'N/A',
        'end_date': aod.aod_end_date.strftime('%d/%m/%Y') if aod.aod_end_date else 'N/A',
        'repay_day': aod.repayment_date.strftime('%d') if aod.repayment_date else '20',
        'aod_amount': str(aod.aod_amount),
        'repay_amount': str(aod.repay_amount),
        'aod_status': aod.aod_status,
        'current_status': aod.current_status,
        'installments': installments
    }
    return JsonResponse(data)

def pfa_list(request):
    """PFA Master List with multi-column filtering, pagination, and export."""
    
    # 1. Base Queryset
    records = Pfa.objects.all().order_by('-determination_due_date')

    # 2. Get Filter Parameters
    f_pfa_no = request.GET.get('pfa_no')
    f_status = request.GET.get('status')
    f_type = request.GET.get('type')
    f_sched_status = request.GET.get('sched_status')
    f_sched_due = request.GET.get('sched_due')
    f_pfa_due = request.GET.get('pfa_due')

    # 3. Apply Filters
    if f_pfa_no:
        records = records.filter(pfa_number__icontains=f_pfa_no)
    if f_status:
        records = records.filter(pfa_status__icontains=f_status)
    if f_type:
        records = records.filter(pfa_type__icontains=f_type)
    if f_sched_status:
        records = records.filter(schedule_status__icontains=f_sched_status)
    if f_sched_due:
        records = records.filter(schedule_due=f_sched_due)
    if f_pfa_due:
        records = records.filter(determination_due_date=f_pfa_due)

    # 4. Handle Excel Export
    if 'export' in request.GET:
        return export_pfa_list(records)

    # 5. Pagination (25 per page)
    paginator = Paginator(records, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Efficiently map Levy Names to the current page only
    levy_nums = [r.levy_number for r in page_obj]
    levy_names = {l.levy_number: l.levy_name for l in LevyData.objects.filter(levy_number__in=levy_nums)}
    
    for r in page_obj:
        r.levy_name = levy_names.get(r.levy_number, "Unknown")

    # Get unique statuses/types for dropdowns
    pfa_statuses = Pfa.objects.values_list('pfa_status', flat=True).distinct()
    sched_statuses = Pfa.objects.values_list('schedule_status', flat=True).distinct()

    context = {
        'page_obj': page_obj,
        'pfa_statuses': pfa_statuses,
        'sched_statuses': sched_statuses,
    }
    return render(request, 'pfa_detail.html', context)

def export_pfa_list(queryset):
    """Excel export for filtered PFA records."""
    levy_names = {l.levy_number: l.levy_name for l in LevyData.objects.all()}
    
    data = []
    for r in queryset:
        data.append({
            'Levy Number': r.levy_number,
            'Levy Name': levy_names.get(r.levy_number, "Unknown"),
            'PFA Number': r.pfa_number,
            'PFA Status': r.pfa_status,
            'PFA Type': r.pfa_type,
            'Schedule Status': r.schedule_status,
            'Schedule Due': r.schedule_due.strftime('%d/%m/%Y') if r.schedule_due else '',
            'PFA Due Date': r.determination_due_date.strftime('%d/%m/%Y') if r.determination_due_date else ''
        })

    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=PFA_Master_Export_{datetime.now().strftime("%Y%m%d")}.xlsx'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='PFA List')
    
    return response

def get_pfa_detail_ajax(request, pfa_number):
    """Fetches PFA details safely even if multiple records exist with the same PFA number."""
    # Use filter().first() instead of get() to prevent the MultipleObjectsReturned error
    pfa = Pfa.objects.filter(pfa_number=pfa_number).first()
    
    if not pfa:
        return JsonResponse({'error': 'PFA not found'}, status=404)

    levy = LevyData.objects.filter(levy_number=pfa.levy_number).first()

    # Fetch notes
    notes = list(ClientNotes.objects.filter(levy_number=pfa.levy_number).values(
        'notes_text', 'user', 'date'
    ))

    data = {
        'pfa_number': pfa.pfa_number,
        'levy_number': pfa.levy_number,
        'levy_name': levy.levy_name if levy else "Unknown",
        'determination_period': pfa.determination_periods,
        # Using getattr to handle potential missing fields in unmanaged models
        'signed_date': pfa.determination_signed_date.strftime('%d/%m/%Y') if hasattr(pfa, 'determination_signed_date') and pfa.determination_signed_date else 'N/A',
        'due_date': pfa.determination_due_date.strftime('%d/%m/%Y') if pfa.determination_due_date else 'N/A',
        'pfa_status': pfa.pfa_status,
        'pfa_type': pfa.pfa_type,
        'schedule_status': pfa.schedule_status,
        'schedule_due': pfa.schedule_due.strftime('%d/%m/%Y') if hasattr(pfa, 'schedule_due') and pfa.schedule_due else 'N/A',
        'amount': str(getattr(pfa, 'determination_amount', '0.00')),
        'lpi_amount': str(getattr(pfa, 'determination_lpi_amount', '0.00')),
        'notes': notes
    }
    return JsonResponse(data)

def lpi_list(request):
    """LPI list with search, pagination, and export."""
    
    # 1. Base Queryset
    records = Lpi.objects.all().order_by('-lpi_create_date')

    # 2. Get Filter Parameters
    f_levy = request.GET.get('levy')
    f_ref = request.GET.get('reference')

    # 3. Apply Filters
    if f_levy:
        records = records.filter(employer_number__icontains=f_levy)
    if f_ref:
        records = records.filter(reference__icontains=f_ref)

    # 4. Handle Export (Before Pagination)
    if 'export' in request.GET:
        return export_lpi_list(records)

    # 5. Pagination (25 per page)
    paginator = Paginator(records, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'lpi_detail.html', {
        'page_obj': page_obj
    })

def export_lpi_list(queryset):
    """Excel export for filtered LPI records."""
    data = list(queryset.values(
        'employer_number', 'reference', 'fiscal_date', 
        'lpi_raised_amount', 'contribution_amount', 
        'late_payment_contribution_amount', 'lpi_calculation_date', 'lpi_create_date'
    ))
    df = pd.DataFrame(data)
    
    # Rename for professional Excel output
    df.columns = [
        'Levy Number', 'LPI Reference', 'Fiscal Date', 
        'LPI Raised', 'Total Contribution', 'Late Contribution', 
        'LPI Calc Date', 'LPI Create Date'
    ]

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=LPI_Export_{datetime.now().strftime("%Y%m%d")}.xlsx'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    return response

def import_lpi_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        
        try:
            # Read Excel file
            df = pd.read_excel(excel_file)

            # Clean column names (strip whitespace)
            df.columns = df.columns.str.strip()

            lpi_instances = []
            for _, row in df.iterrows():
                # Helper function to strip single quotes and whitespace
                def clean(val):
                    if pd.isna(val): return None
                    return str(val).lstrip("'").strip()

                # Helper to handle date conversion (DD/MM/YYYY)
                def parse_date(date_val):
                    if pd.isna(date_val) or not date_val: return None
                    if isinstance(date_val, datetime): return date_val.date()
                    try:
                        return datetime.strptime(clean(date_val), '%d/%m/%Y').date()
                    except (ValueError, TypeError):
                        return None

                # Create LPI instance
                lpi_instances.append(Lpi(
                    employer_number=clean(row.get('Employer Number')),
                    employer_name=clean(row.get('Employer Name')),
                    fiscal_date=parse_date(row.get('Fiscal Date')),
                    reference=clean(row.get('Reference')),
                    lpi_raised_amount=row.get('Lpi Raised Amount', 0),
                    contribution_amount=row.get('Contribution Amount', 0),
                    late_payment_contribution_amount=row.get('Late Payment Contribution Amount', 0),
                    lpi_calculation_date=parse_date(row.get('Lpi Calculation Date')),
                    lpi_end_date=parse_date(row.get('Lpi End Date')),
                    lpi_create_date=parse_date(row.get('Lpi Create Date')),
                ))

            # Bulk create for performance
            if lpi_instances:
                Lpi.objects.bulk_create(lpi_instances)
                messages.success(request, f"Successfully imported {len(lpi_instances)} LPI records.")
            
            return redirect('lpi_list')

        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            
    return render(request, 'import_lpi.html')

def create_aod(request, levy_number):
    levy = get_object_or_404(LevyData, levy_number=levy_number)
    
    if request.method == 'POST':
        Aod.objects.create(
            levy_number=levy_number,
            aod_number=request.POST.get('aod_number'),
            aod_amount=request.POST.get('aod_amount'),
            repay_amount=request.POST.get('repay_amount'),
            aod_status=request.POST.get('aod_status'),
            current_status=request.POST.get('current_status'),
            repayment_date=request.POST.get('repayment_day'),
            aod_start_date=request.POST.get('start_date') or None,
            aod_end_date=request.POST.get('end_date') or None,
            # Process the file upload here
            attachment=request.FILES.get('attachment') 
        )
        return redirect('attorney_list')

    return render(request, 'create_aod.html', {'levy': levy})

def create_pfa(request, levy_number):
    levy = get_object_or_404(LevyData, levy_number=levy_number)
    
    if request.method == 'POST':
        Pfa.objects.create(
            levy_number=levy_number,
            pfa_number=request.POST.get('pfa_number'),
            pfa_status=request.POST.get('pfa_status'),
            pfa_type=request.POST.get('pfa_type'),
            determination_periods=request.POST.get('periods'),
            determination_due_date=request.POST.get('due_date') or None,
            schedule_status=request.POST.get('schedule_status'),
            # Process the file upload here
            attachment=request.FILES.get('attachment')
        )
        return redirect('attorney_list')

    return render(request, 'create_pfa.html', {'levy': levy})

def export_masterfile_excel(request):
    # 1. Fetch Base Levy Data
    levy_qs = LevyData.objects.all().values()
    df_levy = pd.DataFrame(list(levy_qs))

    if df_levy.empty:
        return HttpResponse("No data found in LevyData table.")

    # 2. Aggregations (Subqueries for latest status)
    latest_org_subquery = Org.objects.filter(
        levy_number=OuterRef('levy_number')
    ).order_by('-import_date')
    
    org_agg = Org.objects.values('levy_number').annotate(
        total_due=Sum('due_amount'),
        total_overs=Sum('overs_unders'),
        latest_fiscal=Max('billing_period'),
        current_cbr=Subquery(latest_org_subquery.values('cbr_status')[:1])
    )
    df_org = pd.DataFrame(list(org_agg))

    lpi_agg = Lpi.objects.values('employer_number').annotate(
        total_lpi=Sum('lpi_raised_amount')
    )
    df_lpi = pd.DataFrame(list(lpi_agg))

    bank_agg = BankLine.objects.filter(Recon='No').values('Levy_number').annotate(
        unallocated=Sum('Amount')
    )
    df_bank = pd.DataFrame(list(bank_agg))

    # 3. Merging and Mapping
    df_levy['levy_number'] = df_levy['levy_number'].astype(str)
    
    if not df_org.empty:
        df_org['levy_number'] = df_org['levy_number'].astype(str)
        df_levy = pd.merge(df_levy, df_org, on='levy_number', how='left')
    
    if not df_lpi.empty:
        df_lpi['employer_number'] = df_lpi['employer_number'].astype(str)
        df_levy = pd.merge(df_levy, df_lpi, left_on='levy_number', right_on='employer_number', how='left')
        
    if not df_bank.empty:
        df_bank['Levy_number'] = df_bank['Levy_number'].astype(str)
        df_levy = pd.merge(df_levy, df_bank, left_on='levy_number', right_on='Levy_number', how='left')

    df_levy['Fiscal'] = df_levy.get('latest_fiscal', '')
    df_levy['Due Amount'] = df_levy.get('total_due', 0)
    df_levy['CBR Status'] = df_levy.get('current_cbr', 'T.M.P.') 
    df_levy['Total LPI Outstanding'] = df_levy.get('total_lpi', 0)
    df_levy['Total Unallocated Deposits'] = df_levy.get('unallocated', 0)
    df_levy['Overs & Unders'] = df_levy.get('total_overs', 0)

    # 4. Final Column Selection (Corrected levy_user typo)
    cols_to_export = [
        'levy_number', 'levy_name', 'mip_status', 'commencement_date', 'termination_date',
        'responsible_person', 'responsible_person_id', 'responsible_person_email',
        'responsible_person_cell', 'responsible_person_address', 'registration_number',
        'fica', 'levy_user', 'user_login', 'levy_user_2', 'user_login_2', 'notice_email',
        'telephone', 'postal_address', 'physical_address', 'director_name_1', 'director_mail_1',
        'director_cell_1', 'director_address_1', 'director_name_2', 'director_mail_2',
        'director_cell_2', 'director_address_2', 'director_name_3', 'director_mail_3',
        'director_cell_3', 'director_address_3', 'director_name_4', 'director_mail_4',
        'director_cell_4', 'director_address_4', 'Fiscal', 'Due Amount', 'CBR Status',
        'Total LPI Outstanding', 'Total Unallocated Deposits', 'Overs & Unders',
        'administrator', 'termination_reason', 'termination_status', 'attorney_case', 'attorneys'
    ]

    final_df = df_levy[cols_to_export].fillna(0)

    # 5. Create Excel Response with Date Header
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=TSRF_Masterfile_{datetime.now().strftime("%Y%m%d")}.xlsx'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        # Write the dataframe starting from row 2 (index 1) to leave room for the header
        final_df.to_excel(writer, index=False, sheet_name='Masterfile', startrow=1)
        
        # Access the openpyxl worksheet object to add the header
        workbook = writer.book
        worksheet = writer.sheets['Masterfile']
        
        # Add the custom header in cell A1
        gen_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        header_text = f"TSRF Masterfile - Generated on: {gen_time}"
        worksheet['A1'] = header_text
        
        # Optional: Bold the header
        from openpyxl.styles import Font
        worksheet['A1'].font = Font(bold=True, size=12)

    return response