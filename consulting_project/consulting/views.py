from importlib.resources import files
import json
import datetime as dt
from datetime import date, datetime
import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt 
from django.db import IntegrityError, transaction
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required

# --- Consolidated Imports ---
from .models import (
    ClientClient, 
    ClientContact, 
    ClientInteractionNote, 
    ClientReminder,
    FicaAddress, 
    FicaResponsiblePerson, 
    FicaDirector, 
    FicaBeneficialOwner,
    ClientRiskRating,  # Added Risk Rating Model
    Lead,
    Reminders,
    Claims,
    ClaimsNotes
)

# --- Constants ---
CONSULTANTS = ['Awie de Swardt', 'Marika Botha', 'Stephan de Waal', 'Merri Fennesy']
CLAIM_TYPES = [
    'Funeral - main member', 'Funeral - spouse', 'Funeral - child', 'Funeral - family',
    'Normal Withdrawal', 'Divorce', 'Disability', 'Temporary Disability', 'Death', 'Retirement'
]
INSURERS = ['Sanlam', 'Momentum', 'Old Mutual', 'Hollard', 'Triarc', 'Acravest', 'Liberty Life', 'Alan Gray', 'TSA']

# ------------------------------------------------------
# Helper Functions
# ------------------------------------------------------

def get_next_client_number():
    """Fetches the latest client number and increments it (e.g., FUT00001 -> FUT00002)."""
    try:
        last_client = ClientClient.objects.order_by('-future_client_number').first()
        if last_client and last_client.future_client_number and last_client.future_client_number.startswith('FUT'):
            last_number_str = last_client.future_client_number[3:]
            last_number = int(last_number_str)
            return f"FUT{last_number + 1:05d}"
    except Exception as e:
        print(f"Error generating client number: {e}")
    return "FUT00001"

def safe_parse_date(date_string):
    """Parses DD/MM/YYYY to YYYY-MM-DD format (Python Date Object)."""
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%d/%m/%Y').date()
    except ValueError:
        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except ValueError:
            return None

def parse_repeating_data(request, prefix, fields, file_fields=None):
    """
    Parses dynamic repeating form data.
    Robustly handles 'contact-name-0' (hyphen) and 'dir_name_0' (underscore) differences.
    """
    data = request.POST
    files = request.FILES
    items = []
    index = 0
    
    # Determine separator based on prefix (Contacts use hyphens, FICA entities use underscores in your HTML)
    separator = "-" if prefix == "contact" else "_"

    while True:
        # Check if the primary identifier exists (e.g., contact-name-0 or dir_name_0)
        name_key = f"{prefix}{separator}name{separator}{index}"
        
        # If we can't find the name key, assume end of list
        if name_key not in data:
            if index > 50: break # Safety break
            if index == 0: break # List is empty
            break

        row_data = {}
        
        # 1. Parse Text Fields
        for field in fields:
            key = f"{prefix}{separator}{field}{separator}{index}"
            val = data.get(key, '')
            
            # Handle Checkboxes (returns 'on' or None) and Yes/No radios
            if field.endswith('_q'):
                row_data[field] = (val == 'Yes')
            else:
                row_data[field] = val

        # 2. Parse File Fields (if any)
        if file_fields:
            for file_key_name in file_fields:
                file_input_name = f"{prefix}{separator}{file_key_name}{separator}{index}"
                if file_input_name in files:
                    row_data[file_key_name] = files[file_input_name]

        items.append(row_data)
        index += 1
    return items

# ------------------------------------------------------
# Core Client Views
# ------------------------------------------------------

def home_view(request):
    return render(request, 'consulting/home.html', {})

@login_required
def consulting_home(request):
    # Fetch today's reminders for the popup
    reminders = ClientReminder.objects.filter(
        reminder_date=date.today(), 
        is_dismissed=False
    )
    return render(request, 'consulting/home.html', {'reminders': reminders})

def client_list_view(request):
    clients = ClientClient.objects.all().order_by('client_name')
    return render(request, 'consulting/client_list.html', {'clients': clients})

def client_info_view(request, client_code):
    """Detail view fetching ALL related FICA data including Risk Ratings."""
    client = get_object_or_404(
        ClientClient.objects.prefetch_related(
            'clientcontact_set', 'ficaaddress_set', 'ficadirector_set', 
            'ficabeneficialowner_set', 'ficaresponsibleperson_set',
            'clientriskrating_set' # Added risk rating prefetch
        ), 
        future_client_number=client_code
    )
    
    client_notes = ClientInteractionNote.objects.filter(client=client).order_by('-created_at')
    client_contacts = client.clientcontact_set.all().order_by('id')
    fica_addresses = client.ficaaddress_set.all().order_by('id')
    fica_resp_person = client.ficaresponsibleperson_set.all().order_by('id')
    fica_directors = client.ficadirector_set.all().order_by('id')
    fica_owners = client.ficabeneficialowner_set.all().order_by('id')
    risk_data = client.clientriskrating_set.all().order_by('id') # Fetch risk data
    
    physical_addr = fica_addresses.filter(address_type='physical').first()
    postal_addr = fica_addresses.filter(address_type='postal').first()

    context = {
        'client': client,
        'client_notes': client_notes,
        'client_contacts': client_contacts,
        'physical_addr': physical_addr,
        'postal_addr': postal_addr,
        'fica_resp_person': fica_resp_person, 
        'fica_directors': fica_directors,
        'fica_owners': fica_owners,
        'risk_data': risk_data, # Added to context
        'date_added_formatted': client.date_added.strftime('%d/%m/%Y') if client.date_added else '',
        'declaration_date_formatted': client.declaration_date.strftime('%d/%m/%Y') if client.declaration_date else '',
    }
    return render(request, 'consulting/client_info.html', context)

@require_http_methods(["GET", "POST"])
def edit_client_view(request, client_code):
    client = get_object_or_404(ClientClient, future_client_number=client_code)

    if request.method == 'POST':
        data = request.POST
        files = request.FILES

        try:
            with transaction.atomic():
                # ============================================
                # 1. UPDATE CORE CLIENT FIELDS
                # ============================================
                client.client_name = data.get('client_name')
                client.consultant = data.get('consultant')
                client.industry = data.get('industry')
                client.status = data.get('status')
                client.date_added = safe_parse_date(data.get('date'))
                client.years_active = data.get('years')
                client.employees = data.get('employees') or 0
                
                # Product & Agreement
                client.product = data.get('product')
                client.third_party_contract = (data.get('third_party_contract') == 'yes')
                client.third_party_contact = data.get('third_party_contact')
                client.administrator = data.get('administrator')
                client.umbrella_fund = data.get('umbrella_fund')
                client.insurer = data.get('insurer')
                client.assets = data.get('assets')
                
                # Checkbox/Radio logic
                client.consulting_letter_status = (data.get('consulting_letter') == 'yes')
                client.sla_status = (data.get('sla') == 'yes')
                client.third_party_doc_status = (data.get('third_party_doc') == 'yes')

                # FICA Core Info
                client.company_type = data.get('company_type')
                client.company_registration_number = data.get('reg_number')
                client.contact_number1 = data.get('contact1')
                client.contact_number2 = data.get('contact2')
                client.contact_email1 = data.get('email1')
                client.benefit_note = data.get('benefit_note')
                
                # Risk Rating Global Value
                client.risk_rating = data.get('final_risk_rating', 'Low')
                
                # FICA Step 6 (Nature of Relationship)
                client.nature_of_relationship = data.get('nat_rel')
                client.purpose_of_relationship = data.get('purp_rel')
                client.source_of_funds = data.get('source_funds')
                
                # Declaration
                client.due_diligence_form_name = data.get('due_diligence_form_name')
                client.declaration_name = data.get('declaration_name')
                client.declaration_delegation = data.get('declaration_delegation')
                client.declaration_date = safe_parse_date(data.get('declaration_date'))

                # --- Core File Uploads ---
                if 'consulting_letter_file' in files: client.consulting_letter_file = files['consulting_letter_file']
                if 'sla_file' in files: client.sla_file = files['sla_file']
                if 'third_party_doc_file' in files: client.third_party_doc_file = files['third_party_doc_file']
                if 'reg_docs' in files: client.reg_docs_file = files['reg_docs']
                if 'proof_address' in files: client.proof_address_file = files['proof_address']
                if 'signed_form_upload' in files: client.signed_form_upload = files['signed_form_upload']

                client.save()

                # ============================================
                # 2. UPDATE COMPANY ADDRESSES
                # ============================================
                FicaAddress.objects.filter(client=client).delete()

                # Physical Address
                FicaAddress.objects.create(
                    client=client,
                    address_type='physical',
                    line1=data.get('physical_line1'),
                    line2=data.get('physical_line2'),
                    city=data.get('physical_city'),
                    province=data.get('physical_province'),
                    suburb=data.get('physical_suburb'),
                    postal_code=data.get('physical_code')
                )

                # Postal Address (Only if NOT "Same as physical")
                if not data.get('same_as_physical'):
                    FicaAddress.objects.create(
                        client=client,
                        address_type='postal',
                        line1=data.get('postal_line1'),
                        line2=data.get('postal_line2'),
                        city=data.get('postal_city'),
                        province=data.get('postal_province'),
                        suburb=data.get('postal_suburb'),
                        postal_code=data.get('postal_code')
                    )

                # ============================================
                # 3. UPDATE CONTACTS (Tab 2)
                # ============================================
                ClientContact.objects.filter(client=client).delete()
                
                contact_fields = ['name', 'surname', 'job_title', 'email', 'cell', 'landline', 'birthday', 'interests', 'notes', 
                                  'phys_line1', 'phys_line2', 'phys_city', 'phys_province',
                                  'postal_line1', 'postal_line2', 'postal_city', 'postal_province']
                
                contacts_data = parse_repeating_data(request, 'contact', contact_fields)
                
                for c in contacts_data:
                    if c['name']: 
                        ClientContact.objects.create(
                            client=client,
                            name=c['name'],
                            surname=c['surname'],
                            job_title=c['job_title'],
                            email=c['email'],
                            cell_no=c['cell'],
                            landline=c['landline'],
                            birthday=c['birthday'],
                            interests=c['interests'],
                            notes=c['notes'],
                            physical_address=c['phys_line1'],
                            city_town=c['phys_city'],
                            province=c['phys_province'],
                            postal_address=c['postal_line1']
                        )

                # ============================================
                # 4. RESPONSIBLE PERSONS
                # ============================================
                FicaResponsiblePerson.objects.filter(client=client).delete()
                
                resp_fields = ['name', 'surname', 'designation', 'contact', 'email', 'id_num',
                               'line1', 'line2', 'city', 'province', 'suburb', 'code']
                resp_files = ['circular_upload', 'doc_signed_upload']
                
                resp_data = parse_repeating_data(request, 'resp', resp_fields, resp_files)
                
                for r in resp_data:
                    if r['name']:
                        new_resp = FicaResponsiblePerson(
                            client=client,
                            name=r['name'],
                            surname=r['surname'],
                            designation=r['designation'],
                            contact_number=r['contact'],
                            email_address=r['email'],
                            id_number=r['id_num'],
                            resp_line1=r['line1'],
                            resp_line2=r['line2'],
                            resp_city=r['city'],
                            resp_province=r['province'],
                            resp_suburb=r['suburb'],
                            resp_code=r['code']
                        )
                        if 'circular_upload' in r: new_resp.circular_upload_file = r['circular_upload']
                        if 'doc_signed_upload' in r: new_resp.doc_signed_upload_file = r['doc_signed_upload']
                        new_resp.save()

                # ============================================
                # 5. DIRECTORS & RISK RATINGS
                # ============================================
                FicaDirector.objects.filter(client=client).delete()
                
                dir_fields = [
                    'name', 'surname', 'contact', 'email', 'id', 'designation',
                    'phys_line1', 'phys_line2', 'phys_province', 'phys_city', 'phys_suburb', 'phys_code',
                    'postal_line1', 'postal_line2', 'postal_province', 'postal_city', 'postal_suburb', 'postal_code',
                    'pep_q', 'pep_reason', 'pip_q', 'pip_reason', 'ppo_q', 'ppo_reason', 'kca_q', 'kca_reason'
                ]
                dir_files = ['proof_addr', 'id_copy'] 
                
                dir_data = parse_repeating_data(request, 'dir', dir_fields, dir_files)
                
                for d in dir_data:
                    if d['name']:
                        new_dir = FicaDirector(
                            client=client,
                            name=d['name'],
                            surname=d['surname'],
                            contact_number=d['contact'],
                            email_address=d['email'],
                            id_number=d['id'],
                            designation=d['designation'],
                            
                            phys_line1=d['phys_line1'], phys_line2=d['phys_line2'],
                            phys_city=d['phys_city'], phys_province=d['phys_province'],
                            phys_suburb=d['phys_suburb'], phys_code=d['phys_code'],

                            postal_line1=d['postal_line1'], postal_line2=d['postal_line2'],
                            postal_city=d['postal_city'], postal_province=d['postal_province'],
                            postal_suburb=d['postal_suburb'], postal_code=d['postal_code'],

                            is_pep=(d.get('pep_q') == True), pep_reason=d.get('pep_reason'),
                            is_pip=(d.get('pip_q') == True), pip_reason=d.get('pip_reason'),
                            is_ppo=(d.get('ppo_q') == True), ppo_reason=d.get('ppo_reason'),
                            is_kca=(d.get('kca_q') == True), kca_reason=d.get('kca_reason'),
                        )

                        if 'proof_addr' in d: new_dir.proof_addr_file = d['proof_addr']
                        if 'id_copy' in d: new_dir.id_copy_file = d['id_copy']
                        new_dir.save()

                # ============================================
                # 6. BENEFICIAL OWNERS
                # ============================================
                FicaBeneficialOwner.objects.filter(client=client).delete()
                
                owner_fields = dir_fields 
                owner_files = dir_files
                
                owner_data = parse_repeating_data(request, 'owner', owner_fields, owner_files)
                
                for o in owner_data:
                    if o['name']:
                        new_owner = FicaBeneficialOwner(
                            client=client,
                            name=o['name'],
                            surname=o['surname'],
                            contact_number=o['contact'],
                            email_address=o['email'],
                            id_number=o['id'],
                            designation=o['designation'],
                            
                            phys_line1=o['phys_line1'], phys_line2=o['phys_line2'],
                            phys_city=o['phys_city'], phys_province=o['phys_province'],
                            phys_suburb=o['phys_suburb'], phys_code=o['phys_code'],

                            postal_line1=o['postal_line1'], postal_line2=o['postal_line2'],
                            postal_city=o['postal_city'], postal_province=o['postal_province'],
                            postal_suburb=o['postal_suburb'], postal_code=o['postal_code'],

                            is_pep=(o.get('pep_q') == True), pep_reason=o.get('pep_reason'),
                            is_pip=(o.get('pip_q') == True), pip_reason=o.get('pip_reason'),
                            is_ppo=(o.get('ppo_q') == True), ppo_reason=o.get('ppo_reason'),
                            is_kca=(o.get('kca_q') == True), kca_reason=o.get('kca_reason'),
                        )

                        if 'proof_addr' in o: new_owner.proof_addr_file = o['proof_addr']
                        if 'id_copy' in o: new_owner.id_copy_file = o['id_copy']
                        new_owner.save()

                # ============================================
                # 7. SAVE INDIVIDUAL RISK RATING SCORES
                # ============================================
                ClientRiskRating.objects.filter(client=client).delete()
                
                risk_indices = request.POST.getlist('risk_person_index')
                for idx in risk_indices:
                    ClientRiskRating.objects.create(
                        client=client,
                        full_name=data.get(f'risk_name_{idx}'),
                        role=data.get(f'risk_role_{idx}'),
                        score=int(data.get(f'risk_score_{idx}', 0)),
                        rating=data.get(f'risk_rating_{idx}', 'Low'),
                        is_non_facing=(data.get(f'q_non_facing_{idx}') == 'true'),
                        is_representative=(data.get(f'q_rep_{idx}') == 'true'),
                        is_dipp=(data.get(f'q_dipp_{idx}') == 'true'),
                        is_fppo=(data.get(f'q_fppo_{idx}') == 'true'),
                        is_sanctioned=(data.get(f'q_sanction_{idx}') == 'true'),
                        is_complex_structure=(data.get(f'q_complex_{idx}') == 'true')
                    )

            messages.success(request, f"Client {client.client_name} updated successfully!")
            return redirect('client_info', client_code=client_code)

        except Exception as e:
            messages.error(request, f"Error updating client: {e}")
            print(f"DEBUG ERROR: {e}") 

    # GET REQUEST
    contacts = ClientContact.objects.filter(client=client)
    addresses = FicaAddress.objects.filter(client=client)
    fica_resp = FicaResponsiblePerson.objects.filter(client=client)
    fica_directors = FicaDirector.objects.filter(client=client)
    fica_owners = FicaBeneficialOwner.objects.filter(client=client)

    context = {
        'client': client,
        'client_contacts': contacts,
        'physical_addr': addresses.filter(address_type='physical').first(),
        'postal_addr': addresses.filter(address_type='postal').first(),
        'fica_resp_person': fica_resp,
        'fica_directors': fica_directors,
        'fica_owners': fica_owners,
        'date_added_formatted': client.date_added.strftime('%d/%m/%Y') if client.date_added else '',
        'declaration_date_formatted': client.declaration_date.strftime('%d/%m/%Y') if client.declaration_date else '',
    }
    
    return render(request, 'consulting/edit_client.html', context)

from django.core.files.storage import default_storage

def handle_file_upload(file_key):
    if file_key in files:
        uploaded_file = files[file_key]
        # Clean the filename: replace spaces with underscores
        clean_name = uploaded_file.name.replace(" ", "_")
        return default_storage.save(clean_name, uploaded_file)
    return None

@require_http_methods(["GET", "POST"])
def add_client_view(request):
    if request.method == 'POST':
        print("--- DEBUG: POST Request Received ---")
        data = request.POST
        files = request.FILES
        client_code = data.get('client_number', get_next_client_number())
        
        try:
            # 1. Manually trigger file saves and store the resulting names
            # We do this outside the transaction to ensure files are written to disk
            def upload_file(key):
                if key in files:
                    uploaded_file = files[key]
                    # This physically writes the file to C:\...\media\
                    # and returns the name (it handles duplicates like file_1.csv automatically)
                    saved_name = default_storage.save(uploaded_file.name, uploaded_file)
                    print(f"DEBUG: Physically saved {saved_name} to media folder.")
                    return saved_name
                return None

            # Pre-save the files
            saved_letter = upload_file('consulting_letter_file')
            saved_sla = upload_file('sla_file')
            saved_third_party = upload_file('third_party_doc_file')

            with transaction.atomic():
                # 2. Create the Client using the names we got from default_storage
                client = ClientClient.objects.create(
                    future_client_number=client_code, 
                    client_name=data.get('client_name'),
                    consultant=data.get('consultant', 'N/A'),
                    industry=data.get('industry'),
                    status=data.get('status', 'Active'),
                    date_added=safe_parse_date(data.get('date')),
                    years_active=int(data.get('years')) if data.get('years') else 0,
                    employees=int(data.get('employees')) if data.get('employees') else 0,
                    
                    # Product & Agreement Details
                    product=data.get('product'),
                    third_party_contract=(data.get('third_party_contract') == 'yes'),
                    third_party_contact=data.get('third_party_contact'),
                    administrator=data.get('administrator'),
                    umbrella_fund=data.get('umbrella_fund'),
                    insurer=data.get('insurer'),
                    assets=data.get('assets'),

                    # Use the names of the files we just physically saved
                    consulting_letter_file=saved_letter,
                    consulting_letter_status=(data.get('consulting_letter') == 'yes'),
                    
                    sla_file=saved_sla,
                    sla_status=(data.get('sla') == 'yes'),
                    
                    third_party_doc_file=saved_third_party,
                    third_party_doc_status=(data.get('third_party_doc') == 'yes'),

                    # FICA Compliance Fields
                    risk_rating=data.get('final_risk_rating', 'Low'),
                    nature_of_relationship=data.get('nat_rel', 'Employer / Pension Fund'),
                    purpose_of_relationship=data.get('purp_rel', 'Employee Pension Fund'),
                    source_of_funds=data.get('source_funds', 'Payroll')
                )

                # 3. Create Physical Address
                FicaAddress.objects.create(
                    client=client, 
                    address_type='physical', 
                    line1=data.get('physical_line1'),
                    line2=data.get('physical_line2'),
                    city=data.get('physical_city'),
                    province=data.get('physical_province'),
                    postal_code=data.get('physical_code')
                )

                # 4. Save Risk Ratings
                risk_indices = request.POST.getlist('risk_person_index')
                for idx in risk_indices:
                    ClientRiskRating.objects.create(
                        client=client,
                        full_name=data.get(f'risk_name_{idx}'),
                        role=data.get(f'risk_role_{idx}', 'Director/Owner'),
                        score=int(data.get(f'risk_score_{idx}', 0)),
                        rating=data.get(f'risk_rating_{idx}', 'Low'),
                        is_non_facing=(data.get(f'q_non_facing_{idx}') == 'true'),
                        is_representative=(data.get(f'q_rep_{idx}') == 'true'),
                        is_dipp=(data.get(f'q_dipp_{idx}') == 'true'),
                        is_fppo=(data.get(f'q_fppo_{idx}') == 'true'),
                        is_sanctioned=(data.get(f'q_sanction_{idx}') == 'true'),
                        is_complex_structure=(data.get(f'q_complex_{idx}') == 'true')
                    )

            print(f"DEBUG: Transaction complete for {client_code}.")
            messages.success(request, f"Successfully added {client_code}")
            return redirect('client_info', client_code=client_code) 

        except Exception as e:
            print(f"--- ERROR: {e} ---")
            traceback.print_exc()
            messages.error(request, f"Database/File Error: {e}")
            
    return render(request, 'consulting/add_new_client.html', {'client_number': get_next_client_number()})
# ------------------------------------------------------
# Lead Section
# ------------------------------------------------------

def lead_list_view(request):
    leads_list = Lead.objects.all().order_by('-date_received')
    return render(request, 'consulting/lead_list.html', {'leads': leads_list})

def lead_info_view(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id)
    return render(request, 'consulting/lead_info.html', {'lead': lead})

@csrf_exempt 
@require_http_methods(["POST"])
def log_lead_note_view(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id)
    try:
        with transaction.atomic():
            note_content = request.POST.get('note_content')
            if not note_content:
                messages.error(request, "Note content cannot be empty.")
                return redirect(f'/leads/{lead_id}/info/#tab2')
            
            timestamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
            new_note_entry = f"\n\n--- LOGGED: {timestamp} ---\nBY: {lead.assigned_to}\nNOTES:\n{note_content}"
            
            lead.internal_notes = (lead.internal_notes or "") + new_note_entry
            lead.last_follow_up = dt.date.today()
            lead.save()
            messages.success(request, "Note logged successfully.")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect(f'/leads/{lead_id}/info/#tab2')

@csrf_exempt 
def add_new_lead_view(request):
    # Define the specific consultant list as requested
    consultants = [
        'Awie de Swardt', 
        'Marida Botha', 
        'Stephan de Waal', 
        'Merril Fennesy'
    ]

    if request.method == 'POST':
        try:
            # Safety measure for unmanaged MySQL tables without AUTO_INCREMENT
            last_lead = Lead.objects.all().order_by('id').last()
            next_id = (last_lead.id + 1) if last_lead else 1

            Lead.objects.create(
                id=next_id,
                lead_received_from=request.POST.get('lead_received_from'),
                company_name=request.POST.get('company_name'),
                contact_person=request.POST.get('contact_person'),
                contact_number=request.POST.get('contact_number'),
                contact_email=request.POST.get('contact_email'),
                product_required=request.POST.get('product_required'),
                internal_notes=request.POST.get('internal_notes', ''),
                date_received=dt.datetime.strptime(request.POST['date_received'], '%Y-%m-%d').date(),
                status='New',
                assigned_to=request.POST.get('assigned_to', 'Unassigned')
            )
            messages.success(request, "Lead created successfully!")
            return redirect('lead_list')
        except Exception as e:
            return render(request, 'consulting/add_new_lead.html', {
                'error_message': f"Database Error: {e}",
                'current_date': request.POST.get('date_received'),
                'consultant_options': consultants
            })
            
    # GET request context
    context = {
        'current_date': dt.date.today().strftime('%Y-%m-%d'),
        'consultant_options': consultants, 
    }
    return render(request, 'consulting/add_new_lead.html', context)

@require_http_methods(["GET", "POST"])
def lead_edit_view(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id)
    if request.method == 'POST':
        lead.company_name = request.POST.get('company_name', lead.company_name)
        lead.status = request.POST.get('status', lead.status)
        lead.save()
        messages.success(request, "Lead updated.")
        return redirect('lead_info', lead_id=lead.id)
    return render(request, 'consulting/edit_lead_info.html', {'lead': lead})

# ------------------------------------------------------
# Claims & Dashboards
# ------------------------------------------------------

# ------------------------------------------------------
# Claims & Dashboards
# ------------------------------------------------------

def claims_dashboard(request):
    claims_queryset = Claims.objects.all().order_by('-created_date')
    all_notes = ClaimsNotes.objects.all().order_by('-created_at')
    
    notes_by_claim = {}
    for note in all_notes:
        note_data = {
            'title': note.note_type if hasattr(note, 'note_type') else 'General Note', 
            'body': note.note_body, 
            'createdBy': note.created_by, 
            'date': note.created_at.strftime("%Y-%m-%d")
        }
        notes_by_claim.setdefault(note.claim_id, []).append(note_data)
        
    claims_list = []
    for c in claims_queryset:
        # We must add ALL fields so the JS popup can read them
        claims_list.append({
            'id': c.id, 
            'memberNo': c.member_no, 
            'firstName': c.first_name, 
            'surname': c.surname,
            'idPassport': c.id_passport if hasattr(c, 'id_passport') else '',
            'employerName': c.employer_name if hasattr(c, 'employer_name') else '',
            'insurer': c.insurer,
            'claimType': c.claim_type,
            'consultant': c.consultant,
            'status': c.status, 
            'lastAction': c.last_action if hasattr(c, 'last_action') else '',
            'initialNotes': c.initial_notes if hasattr(c, 'initial_notes') else '',
            'notes': notes_by_claim.get(c.id, [])
        })
        
    context = {
        'claims': claims_queryset,
        'claims_json': json.dumps(claims_list, default=str),
        'consultants': CONSULTANTS, 
        'insurers': INSURERS, 
        'claim_types': CLAIM_TYPES
    }
    return render(request, 'consulting/claims_dashboard.html', context)

@require_POST
def update_claim_details(request):
    claim_id = request.POST.get('claim_id')
    claim = get_object_or_404(Claims, pk=claim_id)
    try:
        # Update ALL fields from the edit form
        claim.member_no = request.POST.get('member_no')
        claim.id_passport = request.POST.get('id_passport')
        claim.first_name = request.POST.get('first_name')
        claim.surname = request.POST.get('surname')
        claim.claim_type = request.POST.get('claim_type')
        claim.insurer = request.POST.get('insurer')
        claim.consultant = request.POST.get('consultant')
        claim.status = request.POST.get('status')
        claim.initial_notes = request.POST.get('initial_notes')
        
        claim.save()
        messages.success(request, f"Claim #{claim_id} updated.")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect('claims_dashboard')

@require_POST
def create_claim_note(request):
    claim = get_object_or_404(Claims, pk=request.POST.get('note_claim_id'))
    # If your model supports note_type, add it here. otherwise just note_body.
    ClaimsNotes.objects.create(
        claim=claim, 
        note_body=request.POST.get('note_body'),
        # note_type=request.POST.get('note_comm_type'), # Uncomment if model has this field
        created_by=request.user.username if request.user.is_authenticated else "System"
    )
    return redirect('claims_dashboard')

@require_POST
def create_claim_reminder(request):
    claim = get_object_or_404(Claims, pk=request.POST.get('reminder_claim_id'))
    Reminders.objects.create(
        claim=claim, member_no=claim.member_no,
        reminder_date=request.POST.get('reminder_date_hidden'),
        reminder_note=request.POST.get('reminder_note_hidden')
    )
    return redirect('claims_dashboard')

@require_POST
def create_new_claim(request):
    try:
        # Capture ALL fields from the create form
        Claims.objects.create(
            member_no=request.POST.get('new_member_no'),
            id_passport=request.POST.get('new_id_passport'),
            first_name=request.POST.get('new_first_name'),
            surname=request.POST.get('new_surname'),
            employer_code=request.POST.get('new_employer_code'),
            employer_name=request.POST.get('new_employer_name'),
            insurer=request.POST.get('new_insurer'),
            claim_type=request.POST.get('new_claim_type'),
            consultant=request.POST.get('new_consultant'),
            initial_notes=request.POST.get('new_notes'),
            status='Pending',
            created_date=date.today()
        )
        messages.success(request, "New claim created!")
    except Exception as e:
        messages.error(request, f"Error creating claim: {e}")
        print(f"Error: {e}")
    return redirect('claims_dashboard')

@login_required
def dismiss_all_reminders(request):
    if request.method == "POST":
        # Update MySQL to dismiss today's active reminders
        ClientReminder.objects.filter(
            reminder_date=timezone.now().date(),
            is_dismissed=False
        ).update(is_dismissed=True)
        
    return redirect('consulting_home')

## ==========================================
# 2. CALENDAR & FILTERING (Updated for Search, History & Time)
# ==========================================
@login_required
def client_calendar(request):
    # Fetch all clients for the search/dropdown
    clients = ClientClient.objects.all().order_by('client_name')
    
    # 1. TABLE LOGIC (Remains conditional for the UI below the search)
    filter_client_id = request.GET.get('view_client')
    selected_client = None
    if filter_client_id and filter_client_id.strip():
        try:
            selected_client = ClientClient.objects.get(id=filter_client_id)
            reminders_list = ClientReminder.objects.filter(client_id=filter_client_id).order_by('-reminder_date', '-reminder_time') 
        except (ClientClient.DoesNotExist, ValueError):
            reminders_list = ClientReminder.objects.none()
    else:
        reminders_list = ClientReminder.objects.filter(reminder_date__gte=date.today(), is_dismissed=False).order_by('reminder_date', 'reminder_time')

    # 2. MASTER SCHEDULE LOGIC (This is for the Popup)
    # This sees EVERYTHING regardless of what client is selected
    all_reminders_full = ClientReminder.objects.all().select_related('client')

    return render(request, 'calendar.html', {
        'clients': clients,
        'reminders_list': reminders_list,
        'all_reminders_full': all_reminders_full, # THE MASTER LIST
        'selected_client': selected_client
    })

# ==========================================
# 3. ACTIONS (SAVE, DONE, DELETE)
# ==========================================
@login_required
def add_reminder(request):
    if request.method == "POST":
        client_id = request.POST.get('client_id')
        reminder_date = request.POST.get('date')
        reminder_time = request.POST.get('time') # New field from Teams-view slots
        title = request.POST.get('title')
        note = request.POST.get('note')
        reminder_id = request.POST.get('reminder_id') 

        # Clean the time input: if no time is selected, we treat it as an all-day reminder (None)
        if not reminder_time or reminder_time == "undefined":
            reminder_time = None

        if client_id and reminder_date:
            if reminder_id:
                # UPDATE EXISTING logic
                reminder = get_object_or_404(ClientReminder, id=reminder_id)
                reminder.reminder_date = reminder_date
                reminder.reminder_time = reminder_time # Update time
                reminder.title = title
                reminder.note = note
                reminder.save()
                messages.success(request, "Reminder/Meeting updated successfully.")
            else:
                # CREATE NEW logic
                ClientReminder.objects.create(
                    client_id=client_id,
                    title=title,
                    note=note,
                    reminder_date=reminder_date,
                    reminder_time=reminder_time, # Save specific hour
                    created_by=request.user, 
                    is_dismissed=False
                )
                messages.success(request, f"New meeting scheduled for {reminder_date} at {reminder_time or 'All Day'}.")
        
        # Redirect back to the specific client's planner view to keep the workspace open
        return redirect(f"{reverse('client_calendar')}?view_client={client_id}")
        
    return redirect('client_calendar')

@login_required
def dismiss_single_reminder(request, reminder_id):
    if request.method == "POST":
        reminder = get_object_or_404(ClientReminder, id=reminder_id)
        reminder.is_dismissed = True
        reminder.save()
    return redirect('client_calendar')

@login_required
def delete_reminder(request, reminder_id):
    """Permanently deletes a reminder from the database."""
    if request.method == "POST":
        reminder = get_object_or_404(ClientReminder, id=reminder_id)
        reminder.delete()
    
    # Redirect back, staying on the same filtered page if possible
    return redirect(request.META.get('HTTP_REFERER', 'client_calendar'))

@require_POST
def post_client_note(request):
    try:
        # 1. Parse JSON data from the fetch request
        data = json.loads(request.body)
        client_code = data.get('client_code')
        
        # 2. Find the client using the code (e.g., FUT00004)
        client = get_object_or_404(ClientClient, future_client_number=client_code)
        
        # 3. Create the note record
        ClientInteractionNote.objects.create(
            client=client,
            comm_type=data.get('comm_type'),
            note_type=data.get('note_type'),
            note_text=data.get('note_text'),
            created_by=request.user.username if request.user.is_authenticated else "System"
        )
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        print(f"Error saving note: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
import csv
from django.http import StreamingHttpResponse

class Echo:
    """An object that implements just the write method of the file-like interface."""
    def write(self, value):
        return value

@login_required
def export_clients_comprehensive(request):
    """Exports a highly detailed CSV of all clients including primary contacts and FICA info."""
    
    # 1. Setup Headers
    headers = [
        'Client Number', 'Ref No 2', 'Client Name', 'Consultant', 'RISK RATING', 
        'INDUSTRY', 'STATUS', 'START DATE', 'DATE ADDED', 'YEARS ACTIVE', 
        'TOTAL EMPLOYEES', 'PRODUCT TYPE', 'THIRD PARTY CONTRACT', 
        'THIRD PARTY CONTACT', 'Administrator', 'Umbrella Option', 'INSURER', 
        'ASSETS UNDER MANAGEMENT', '3RD PARTY DOCUMENT STATUS', 'CONTACT PERSON NAME', 
        'CONTACT PERSON SURNAME', 'JOB TITLE', 'EMAIL', 'CELL', 'LANDLINE', 
        'BIRTHDAY', 'INTERESTS', 'PHYSICAL ADDRESS LINE 1', 'PHYSICAL ADDRESS LINE 2', 
        'CITY/TOWN', 'PROVINCE', 'POSTAL CODE', 'POSTAL ADDRESS LINE 1', 
        'POSTAL ADDRESS LINE 2', 'CITY/TOWN', 'PROVINCE', 'POSTAL CODE'
    ]

    # 2. Query Data (Optimized with prefetch)
    clients = ClientClient.objects.prefetch_related('clientcontact_set', 'ficaaddress_set').all()

    def rows():
        yield headers
        for c in clients:
            # Get Primary Contact (first one)
            contact = c.clientcontact_set.first()
            # Get Addresses
            phys = c.ficaaddress_set.filter(address_type='physical').first()
            post = c.ficaaddress_set.filter(address_type='postal').first()

            yield [
                c.future_client_number,
                c.id,
                c.client_name,
                c.consultant,
                f"{c.fica_dd_completed}%", # Risk/FICA Rating
                c.industry,
                c.status,
                c.date_added, # Start Date
                c.date_added, # Date Added
                c.years_active,
                c.employees,
                c.product,
                "Yes" if c.third_party_contract else "No",
                c.third_party_contact,
                c.administrator,
                c.umbrella_fund,
                c.insurer,
                c.assets,
                "Yes" if c.third_party_doc_status else "No",
                # Contact Details
                contact.name if contact else "",
                contact.surname if contact else "",
                contact.job_title if contact else "",
                contact.email if contact else "",
                contact.cell_no if contact else "",
                contact.landline if contact else "",
                contact.birthday if contact else "",
                contact.interests if contact else "",
                # Physical Address
                phys.line1 if phys else "",
                phys.line2 if phys else "",
                phys.city if phys else "",
                phys.province if phys else "",
                phys.postal_code if phys else "",
                # Postal Address
                post.line1 if post else "",
                post.line2 if post else "",
                post.city if post else "",
                post.province if post else "",
                post.postal_code if post else "",
            ]

    # 3. Stream the Response
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse(
        (writer.writerow(row) for row in rows()),
        content_type="text/csv",
    )
    response['Content-Disposition'] = f'attachment; filename="Comprehensive_Client_Export_{date.today()}.csv"'
    return response