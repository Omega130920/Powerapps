from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import LevyData, ClientNotes, User
from django.db.models import Q
import csv
import io
from .models import BankLine
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
import datetime
from decimal import Decimal,InvalidOperation
from .models import Org
from .models import LevyData, ClientNotes, BankLine, Org, TsrfPdfDocument 
from .forms import AddLevyForm, DocumentUploadForm 
from django.http import Http404, FileResponse, HttpRequest, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Max, Subquery, OuterRef, F
import os
from .models import OrgNotes
from .services.outlook_graph_service import fetch_inbox_messages, _make_graph_request
from .models import EmailDelegation, DelegationNote, EmailTransaction
from dateutil import parser
from django.conf import settings

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
    """
    View to display a list of all levy records with search and filter functionality,
    annotated with the latest Org data using Subquery.
    """
    search_query = request.GET.get('search_query', '').strip()
    
    # 1. Capture Filter Values
    current_filters = {
        'mip_status_filter': request.GET.get('mip_status_filter', ''),
        'fica_filter': request.GET.get('fica_filter', ''),
        'billing_period_filter': request.GET.get('billing_period_filter', ''), 
        'cbr_status_filter': request.GET.get('cbr_status_filter', ''),
    }

    # 2. Start with all LevyData records
    levy_records = LevyData.objects.all()

    # --- Annotation Logic (REMAINS THE SAME) ---
    latest_org_queryset = Org.objects.filter(
        levy_number=OuterRef('levy_number')
    ).order_by('-billing_period', '-created_at')
    
    levy_records = levy_records.annotate(
        latest_billing_period=Subquery(latest_org_queryset.values('billing_period')[:1]),
        latest_cbr_status=Subquery(latest_org_queryset.values('cbr_status')[:1]),
        latest_overs_unders=Subquery(latest_org_queryset.values('overs_unders')[:1]),
        latest_due_amount=Subquery(latest_org_queryset.values('due_amount')[:1]),
    )
    # --- End Annotation ---
    
    # 3. Apply Filters based on captured values
    if current_filters['mip_status_filter']:
        levy_records = levy_records.filter(mip_status=current_filters['mip_status_filter'])
        
    if current_filters['fica_filter']:
        levy_records = levy_records.filter(fica=current_filters['fica_filter'])
        
    if current_filters['billing_period_filter']:
        # Filter logic must change to check for the Month/Year part if the billing_period is stored as DD/MM/YYYY
        
        # Determine the month/year to filter by, assuming MM/YYYY format from the dropdown
        month_year_filter = current_filters['billing_period_filter']
        
        # Use Q objects to filter the annotated field, checking if it ends with the selected MM/YYYY
        # Example: latest_billing_period LIKE '%/12/2024'
        # NOTE: This assumes the Org billing_period format is consistently DD/MM/YYYY
        levy_records = levy_records.filter(latest_billing_period__endswith=f'/{month_year_filter}')
        
    if current_filters['cbr_status_filter']:
        # Filter on the annotated field
        levy_records = levy_records.filter(latest_cbr_status=current_filters['cbr_status_filter'])


    # 4. Apply general Search Query
    if search_query:
        levy_records = levy_records.filter(
            Q(levy_number__icontains=search_query) |
            Q(levy_name__icontains=search_query)
        )
    
    # Order the results
    levy_records = levy_records.order_by('levy_number')

    
    # 5. Generate unique options for filter dropdowns (Grouping Billing Period by MM/YYYY)
    
    # Get all unique billing period strings from the Org model
    raw_periods = Org.objects.values_list('billing_period', flat=True).distinct().exclude(billing_period__isnull=True).exclude(billing_period='').order_by('-billing_period')
    
    processed_periods = {}
    
    for period_str in raw_periods:
        try:
            # Parse the date string assuming DD/MM/YYYY format
            date_obj = datetime.datetime.strptime(period_str, '%d/%m/%Y').date()
            
            # Format to the desired MM/YYYY string
            month_year_key = date_obj.strftime('%m/%Y')
            
            # Use a dictionary to keep unique Month/Year values, storing the date object
            # to help with final sorting later if needed, but here we only care about uniqueness
            processed_periods[month_year_key] = date_obj 
            
        except ValueError:
            # Skip invalid date strings
            continue
            
    # Sort the unique MM/YYYY strings by their underlying date object (descending)
    sorted_periods = sorted(
        processed_periods.keys(),
        key=lambda k: processed_periods[k],
        reverse=True
    )
    
    filter_options = {
        'mip_statuses': LevyData.objects.values_list('mip_status', flat=True).distinct().exclude(mip_status__isnull=True).exclude(mip_status='').order_by('mip_status'),
        'fica_statuses': LevyData.objects.values_list('fica', flat=True).distinct().exclude(fica__isnull=True).exclude(fica='').order_by('fica'),
        
        # Use the processed list for the dropdown
        'billing_periods': sorted_periods, 
        
        'cbr_statuses': Org.objects.values_list('cbr_status', flat=True).distinct().exclude(cbr_status__isnull=True).exclude(cbr_status='').order_by('cbr_status'),
    }


    context = {
        'levy_records': levy_records,
        'search_query': search_query or '',
        'current_filters': current_filters, 
    }
    context.update(filter_options)
    
    return render(request, 'TSRF_RECON_APP/levy_list.html', context)


@login_required
@transaction.atomic 
def levy_information(request, levy_number):
    """
    View to display detailed information for a single levy record, its notes,
    bank lines, latest Org summary, email logs, and handles PDF upload/download.
    """
    levy_record = get_object_or_404(LevyData, levy_number=levy_number)

    org_summary = None
    try:
        # Fetch the absolute latest ORG data record for this levy number
        org_summary = Org.objects.filter(levy_number=levy_record.levy_number).order_by('-id').first()
    except Exception as e:
        print(f"Error fetching Org summary: {e}") 
        pass
    
    pdf_upload_form = DocumentUploadForm()

    # -----------------------------------------------------------------------
    # 1. Handle POST Requests
    # -----------------------------------------------------------------------
    if request.method == 'POST':
        if 'upload_document' in request.POST:
            pdf_upload_form = DocumentUploadForm(request.POST, request.FILES)
            if pdf_upload_form.is_valid():
                try:
                    document = pdf_upload_form.save(commit=False)
                    document.related_levy_number = levy_number
                    document.uploaded_by = request.user.username if request.user.is_authenticated else 'Unknown User'
                    
                    submitted_title = document.title
                    FICA_COLUMN_MAP = {
                        'Fica_1': 'id_document', 'Fica_2': 'proof_of_address',
                        'Fica_3': 'bank_statement', 'Fica_4': 'appointment_letter',
                        'Fica_5': 'vat_number', 'Fica_6': 'mandate_trust_deed',
                        'Fica_7': 'tax_number',
                    }

                    if submitted_title in FICA_COLUMN_MAP:
                        column_name = FICA_COLUMN_MAP[submitted_title]
                        setattr(document, column_name, '1')
                        document.title = column_name.replace('_', ' ').title() 
                    
                    document.save() 
                    messages.success(request, f'Document "{document.document_file.name}" uploaded successfully.')
                    return redirect(f"{request.path}#pdf-documents")
                except Exception as e:
                    messages.error(request, f"Error saving document: {e}")
            else:
                messages.error(request, 'Document upload failed. Please check the selected file and title.')
                
        elif 'notes_text' in request.POST:
            notes_text = request.POST.get('notes_text')
            if notes_text:
                ClientNotes.objects.create(
                    levy_number=levy_number,
                    notes_text=notes_text,
                    user=request.user.username
                )
                messages.success(request, 'Note added successfully!')
            else:
                messages.error(request, 'Note cannot be empty.')
            return redirect(f"{request.path}#overview")

    # -----------------------------------------------------------------------
    # 2. Handle GET Requests (Downloads)
    # -----------------------------------------------------------------------
    download_id = request.GET.get('download_id')
    if download_id:
        try:
            document = get_object_or_404(
                TsrfPdfDocument, 
                pk=download_id, 
                related_levy_number=levy_number 
            )
            filepath = document.document_file.path
            if not os.path.exists(filepath):
                raise Http404("Document file not found on server.")

            return FileResponse(
                open(filepath, 'rb'), 
                as_attachment=True, 
                filename=os.path.basename(filepath)
            )
        except Exception as e:
            messages.error(request, f'Download failed: {e}')
            return redirect('levy_information', levy_number=levy_number)

    # -----------------------------------------------------------------------
    # 3. Standard Page Load / Context Setup
    # -----------------------------------------------------------------------
    
    # Client Notes
    notes = ClientNotes.objects.filter(levy_number=levy_number).order_by('-date')
    
    # Bank Line Data
    bank_lines = BankLine.objects.filter(Levy_number=levy_number).order_by('-Date')
    
    # PDF Documents
    documents = TsrfPdfDocument.objects.filter(related_levy_number=levy_number).order_by('-uploaded_at')

    # Org Notes History
    org_notes = OrgNotes.objects.filter(Levy_number=levy_number).order_by('-Date')
    latest_org_note_summary = org_notes.first() 

    # 🟢 UPDATED FILTER: Use __icontains to handle trailing spaces in the DB (e.g., "22117 ")
    clean_levy = str(levy_number).strip()
    email_logs = EmailDelegation.objects.filter(company_code__icontains=clean_levy).order_by('-received_at')

    context = {
        'levy_record': levy_record,
        'notes': notes,
        'bank_lines': bank_lines,
        'org_summary': org_summary, 
        'pdf_upload_form': pdf_upload_form,
        'documents': documents,
        'org_notes': org_notes,
        'latest_org_note': latest_org_note_summary,
        'email_logs': email_logs,
    }
    return render(request, 'TSRF_RECON_APP/levy_information.html', context)

@transaction.atomic
def import_data(request):
    """
    Handles CSV file upload, parsing, validation, and database import for BankLine data.
    """
    context = {}

    # 1. Handle POST request (Form Submission)
    if request.method == 'POST':
        if 'import_file' in request.FILES:
            csv_file = request.FILES['import_file']
            
            # Basic file type check
            if not csv_file.name.endswith('.csv'):
                context['error_message'] = 'Invalid file type. Please upload a CSV file.'
                return render(request, 'TSRF_RECON_APP/Import.html', context)
            
            # Get checkbox value (returns 'on' or None)
            has_header = request.POST.get('header_row') is not None
            
            # Read the file content
            try:
                uploaded_file = csv_file.read().decode('latin-1')
            except Exception as e:
                context['error_message'] = f"File reading error (encoding issue?): {e}"
                return render(request, 'TSRF_RECON_APP/Import.html', context)
            
            # Use StringIO to treat the string content as a file for the csv module
            io_string = io.StringIO(uploaded_file)
            reader = csv.reader(io_string)
            
            # Skip the header row if specified
            if has_header:
                try:
                    next(reader) 
                except StopIteration:
                    context['error_message'] = "File is empty or contains only a header."
                    return render(request, 'TSRF_RECON_APP/Import.html', context)

            records_to_create = []
            
            try:
                EXPECTED_COLUMNS = 9 
                successful_count = 0
                line_count = 0

                # Iterate over the remaining rows
                for row in reader:
                    line_count += 1
                    # Filter out completely empty rows
                    if not any(row):
                        continue
                        
                    # 2. Column Count Check
                    if len(row) < EXPECTED_COLUMNS:
                        print(f"Skipping row {line_count} due to insufficient columns ({len(row)} of {EXPECTED_COLUMNS} expected): {row}")
                        continue
                        
                    try:
                        # --- Data Cleansing and Conversion ---
                        transaction_date = datetime.datetime.strptime(row[0].strip(), '%d/%m/%Y').date() 
                        amount_value = Decimal(row[1].strip().replace(',', ''))
                        
                        # --- Model Instantiation and Mapping ---
                        record = BankLine(
                            Date=transaction_date,
                            Amount=amount_value,
                            Reference_Description=row[2].strip(),
                            Other_Reference=row[3].strip() or None, 
                            Recon=row[4].strip() or None,
                            Levy_number=row[5].strip() or None,
                            Fisical=row[6].strip() or None,
                            Type=row[7].strip(),
                            Column_5=row[8].strip() or None,
                            Column_6=None, 
                        )
                        records_to_create.append(record)
                        
                    except ValueError as ve:
                        # Handles conversion errors for Date or Decimal
                        print(f"Data Conversion Error in row {line_count}: {ve} -> Row: {row}")
                        context['warning_message'] = f"Warning: Some rows failed conversion (e.g., date/amount format). Check console for details."
                        continue
                        
                    except Exception as e:
                        # Handles other row-specific errors
                        print(f"Generic Error in row {line_count}: {e} -> Row: {row}")
                        context['warning_message'] = f"Warning: Some rows failed due to an unexpected error. Check console for details."
                        continue
                        
                # --- Database Bulk Creation for performance ---
                
                if records_to_create:
                    BankLine.objects.bulk_create(records_to_create)
                    successful_count = len(records_to_create)

                
                context['success_message'] = f'Successfully processed {successful_count} records.'
                
            except csv.Error as e:
                # Handle general CSV formatting errors (e.g., mismatched delimiters)
                context['error_message'] = f"CSV Parsing Error on line {line_count}: {e}"
                
            except IntegrityError:
                 # Handle database constraint errors
                 context['error_message'] = "A database integrity error occurred. Check for duplicate entries."
                 
            except Exception as e:
                # Catch any unexpected errors during processing
                print(f"CRITICAL ERROR: {e}")
                context['error_message'] = f"An unexpected error occurred during import: {e}"

        else:
            context['error_message'] = 'No file was submitted.'
            
    # 3. Handle GET request (Page Load) or re-render after POST
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
def bank_line_list(request):
    """
    View to display UNALLOCATED BankLine records. (Original name retained).
    Lines are excluded if Levy_number is assigned.
    """
    search_query = request.GET.get('search_query', '').strip()
    
    # Use the helper function for UNALLOCATED lines
    bank_lines = get_bank_line_queryset(allocated=False, search_query=search_query)
        
    paginator = Paginator(bank_lines, 24)
    page_number = request.GET.get('page', 1)
    
    try:
        bank_lines_page = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        bank_lines_page = paginator.page(1)
    
    context = {
        'bank_lines_page': bank_lines_page,
        'search_query': search_query,
        'title': 'Unassigned Bank Lines', # Title for the new template
        'is_allocated_view': False,
    }
    # Render to the new 'unallocated_banklines.html'
    return render(request, 'TSRF_RECON_APP/unallocated_banklines.html', context)


@login_required
def allocated_bank_line_list(request):
    """View to display ALLOCATED bank line records, excluding reconciled ones."""
    search_query = request.GET.get('search_query', '').strip()
    
    # Use the helper function for ALLOCATED lines, which now excludes reconciled Types
    bank_lines = get_bank_line_queryset(allocated=True, search_query=search_query)
        
    paginator = Paginator(bank_lines, 24)
    page_number = request.GET.get('page', 1)
    
    try:
        bank_lines_page = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        bank_lines_page = paginator.page(1)
    
    context = {
        'bank_lines_page': bank_lines_page,
        'search_query': search_query,
        'title': 'Allocated Bank Lines', # Title for the new template
        'is_allocated_view': True,
    }
    # Render to the new 'allocated_banklines.html'
    return render(request, 'TSRF_RECON_APP/allocated_banklines.html', context)


# ... (The remaining views are left as they were in your submission, but the 
# RECONCILED_TYPES constant and logic in get_bank_line_queryset is the core change.) ...

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
    Handles adding a new LevyData record to the external 'levy data' table.
    """
    if request.method == 'POST':
        form = AddLevyForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"New levy '{form.cleaned_data['levy_name']}' added successfully!")
                return redirect('levy_list')
            except IntegrityError:
                messages.error(request, "Error: A levy with that number already exists. Please use a unique Levy Number.")
            except Exception as e:
                messages.error(request, f"Error saving levy: {e}")
                
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = AddLevyForm()

    context = {
        'form': form,
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


@login_required
def bankline_edits_view(request, levy_number):
    """
    Handles displaying and saving edits for a specific BankLine entry.
    """
    # 1. Get the line_id from the query parameters (e.g., ?line_id=301777)
    line_id = request.GET.get('line_id')
    bank_line_entry = None
    
    if line_id:
        try:
            # 2. Query the database for the specific bank line entry
            # Assuming BankLine model is accessible here
            bank_line_entry = BankLine.objects.get(id=line_id)
            
        except BankLine.DoesNotExist:
            bank_line_entry = None
        except ValueError:
            bank_line_entry = None

    # Handle POST requests for saving the form changes
    if request.method == 'POST' and bank_line_entry:
        
        # 🛑 Capture the updated Levy Number (from the editable field)
        bank_line_entry.Levy_number = request.POST.get('levy_number')
        
        # Capture other editable fields:
        bank_line_entry.Recon = request.POST.get('recon_status')
        new_type = request.POST.get('type')
        bank_line_entry.Type = new_type 
        
        # The fiscal year input is a date type, but Django will handle it.
        bank_line_entry.Fisical = request.POST.get('fisical_year')
        bank_line_entry.Column_5 = request.POST.get('note_selection')
        
        # NOTE: Column_6 (Allocation Notes) is currently read-only in the HTML
        # and not posted back to the view, so we omit saving it here.
        # bank_line_entry.Column_6 = request.POST.get('column_6') 
        
        try:
            bank_line_entry.save()
            messages.success(request, f"Bank Line #{bank_line_entry.id} updated successfully!")
            
            # *** REDIRECT LOGIC ***
            # If the line was allocated AND the Type was set to a reconciled value, 
            # redirect the user back to the main allocated list.
            if bank_line_entry.Levy_number and new_type in RECONCILED_TYPES:
                # Assuming 'allocated_bank_line_list' is a defined URL name
                return redirect('allocated_bank_line_list') 
            
        except Exception as e:
            messages.error(request, f"Error saving Bank Line #{bank_line_entry.id}: {e}")
            
        # Default redirect: stay on the same edit page and refresh the GET request
        return redirect(f"{request.path}?line_id={bank_line_entry.id}")

    # 3. Add the retrieved record to the context
    context = {
        'title': f'Bankline Edits for Levy {levy_number}',
        'levy_number': levy_number,
        'bank_line_entry': bank_line_entry,
    }
    
    # Assuming 'TSRF_RECON_APP/bankline_edits.html' is the correct template path
    return render(request, 'TSRF_RECON_APP/bankline_edits.html', context)

@login_required
def assigned_bank_line_list(request):
    """View to display fully assigned (reconciled) bank line records with filtering."""
    
    # 1. Capture All Filters
    wildcard_query = request.GET.get('wildcard_query', '').strip()
    note_selection_filter = request.GET.get('note_selection_filter', '').strip()
    # --- NEW: Capture Type Filter ---
    type_filter = request.GET.get('type_filter', '').strip() 
    
    fisical_start_date_str = request.GET.get('fisical_start_date', '').strip()
    fisical_end_date_str = request.GET.get('fisical_end_date', '').strip()
    
    # Define the *only* strict format reliable for string date range filtering
    STRICT_DATE_FORMAT = '%Y-%m-%d' 
    
    date_range_valid = False
    
    def parse_date_to_string_format(date_str):
        """Attempts to parse any input date string into a YYYY-MM-DD string."""
        # Try YYYY-MM-DD format (standard browser output)
        try:
            return datetime.datetime.strptime(date_str, '%Y-%m-%d').strftime(STRICT_DATE_FORMAT)
        except ValueError:
            pass
        
        # Try DD-MM-YYYY format (user input)
        try:
            # Note: replacing '/' with '-' to handle common user input variations
            return datetime.datetime.strptime(date_str.replace('/', '-'), '%d-%m-%Y').strftime(STRICT_DATE_FORMAT)
        except ValueError:
            pass

        return None # Parsing failed

    fisical_start_date_db = None
    fisical_end_date_db = None
    
    if fisical_start_date_str and fisical_end_date_str:
        
        fisical_start_date_db = parse_date_to_string_format(fisical_start_date_str)
        fisical_end_date_db = parse_date_to_string_format(fisical_end_date_str)

        if fisical_start_date_db and fisical_end_date_db:
            # Simple string comparison to check order before filtering (YYYY-MM-DD makes this reliable)
            if fisical_start_date_db > fisical_end_date_db:
                messages.error(request, "Start date cannot be after the end date.") 
            else:
                date_range_valid = True
        else:
            messages.error(request, "Invalid date format submitted. Please use YYYY-MM-DD or DD-MM-YYYY.")
            
    
    # 2. Base Query: Lines that are allocated AND reconciled
    bank_lines = BankLine.objects.filter(
        Q(Levy_number__isnull=False) & ~Q(Levy_number=''),
        Type__in=RECONCILED_TYPES
    ).order_by('-Date')
    
    # 3. Apply Filters
    
    # 3a. Note Selection Filter (Column_5)
    if note_selection_filter:
        bank_lines = bank_lines.filter(Column_5=note_selection_filter)
    
    # --- NEW: Type Filter ---
    if type_filter:
        bank_lines = bank_lines.filter(Type=type_filter)

    # 3b. Fisical Date Range Filter (based on Fisical string field)
    if date_range_valid:
        bank_lines = bank_lines.filter(
            Fisical__gte=fisical_start_date_db,
            Fisical__lte=fisical_end_date_db
        )

    # 3c. Wildcard Search (Levy, Description, Amount, etc.)
    if wildcard_query:
        # Build Q object for a comprehensive search across key display fields
        bank_lines = bank_lines.filter(
            Q(Levy_number__icontains=wildcard_query) |
            Q(Reference_Description__icontains=wildcard_query) |
            Q(Amount__icontains=wildcard_query) |
            Q(Fisical__icontains=wildcard_query) |
            Q(Type__icontains=wildcard_query) |
            Q(Column_5__icontains=wildcard_query)
        )
        
    # 4. Pagination (UNCHANGED)
    paginator = Paginator(bank_lines, 24)
    page_number = request.GET.get('page', 1)
    
    try:
        bank_lines_page = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        bank_lines_page = paginator.page(1)
    
    # 5. Generate Options
    
    # The list of available types for the dropdown:
    type_options = RECONCILED_TYPES 

    note_options = [
        "AOD CONRIBUTIONS", "AOD LPI", 
        "DEPSOSIT FOR CURRENT FISCAL - PREVIOUS FISCAL NOT RECONCILED", 
        "DIFFERENCE TO FINALISED BILL AND PAYMENT", "EMPLOYER TO FINALISE", 
        "EMPLOYER TO FINALISE & FW POP", "EMPLOYER TO FW POP", "LPI - REQUESTED POP", 
        "LPI - SHORT - PAID LATE", "RECONSILED", "REFUND PAID", 
        "REFUND REQUESTED", "REQUESTED SUPPORTING DOCUMENTS", 
        "SINGLE MEMBER PAYMENT", "SYSTEM ISSUE"
    ]
    
    context = {
        'bank_lines_page': bank_lines_page,
        'wildcard_query': wildcard_query,
        'note_selection_filter': note_selection_filter,
        # --- NEW: Pass Type Context ---
        'type_filter': type_filter,
        'type_options': type_options,
        
        'fisical_start_date': fisical_start_date_str, 
        'fisical_end_date': fisical_end_date_str,
        'note_options': note_options,
        'title': 'Assigned Bank Lines', 
    }
    return render(request, 'TSRF_RECON_APP/reconciled_banklines.html', context)

@login_required
def org_table_info(request, levy_number):
    """
    Displays detail for a single Org record (the latest one) and handles 
    the submission of new OrgNotes for that levy number.
    """
    # 1. Determine the latest import date across ALL Org records
    # This aggregate query runs successfully on its own.
    latest_import_data = Org.objects.aggregate(Max('created_at'))
    latest_datetime = latest_import_data.get('created_at__max')

    # Ensure we have a latest date before proceeding
    if not latest_datetime:
        messages.error(request, f"No import data found for ORG records.")
        return redirect('org_table_view')

    # 2. Fetch the specific Org record:
    #    - Filter by the provided levy_number
    #    - Filter by the latest import datetime found in step 1
    #    - Use .get() instead of get_object_or_404(queryset) 
    #      as .get() is sufficient after filtering and avoids queryset confusion.
    #    - If multiple records match (unlikely if created_at is exact), .order_by('-id') 
    #      ensures deterministic selection.

    try:
        org_record = Org.objects.filter(
            levy_number=levy_number, 
            created_at=latest_datetime
        ).order_by('-id').first() # Use .first() to get the object, or None

        if not org_record:
            # If a record isn't found for the latest import date, 
            # maybe the latest record is from an older batch, so we fetch the absolute latest
            org_record = get_object_or_404(
                Org.objects.filter(levy_number=levy_number).order_by('-created_at', '-id')
            )
            
    except Org.DoesNotExist:
        raise Http404(f"ORG Record not found for Levy {levy_number}.")


    # 3. Fetch all existing notes for this levy number, ordered newest first
    org_notes = OrgNotes.objects.filter(Levy_number=levy_number).order_by('-Date')
    
    # 4. Handle POST request (Note Submission) - remains unchanged
    if request.method == 'POST':
        note_text = request.POST.get('notes_text')
        
        if note_text:
            try:
                fiscal_date_str = org_record.billing_period
                date_obj = None
                if fiscal_date_str:
                    try:
                        date_obj = datetime.datetime.strptime(fiscal_date_str, '%d/%m/%Y').date()
                    except ValueError:
                        pass
                
                OrgNotes.objects.create(
                    Levy_number=levy_number,
                    Date=datetime.datetime.now(), 
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
            
    # 5. Context for GET request (initial load or after POST failure)
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