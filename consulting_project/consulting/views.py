import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt 
from django.db import IntegrityError, transaction
from django.contrib import messages
from datetime import date, datetime, timezone
import datetime as dt # Use dt for datetime module to avoid conflict with datetime.datetime import

# Import all models
from .models import (
    ClientClient, 
    ClientContact, 
    FicaAddress, 
    FicaResponsiblePerson, 
    FicaDirector, 
    FicaBeneficialOwner,
    Lead,
    Reminders # Now used for real database interaction
)

# --- MOCK DATA REMOVED ---
# DUMMY_CLIENTS_DATA and all Lead mock data removed as requested.
# ---------------------------------------------------------

# --- Helper Function to generate next sequential client number ---
def get_next_client_number():
    """Fetches the latest client number and increments it (e.g., FUT00001 -> FUT00002)."""
    try:
        # Get the latest future_client_number, ordered descending
        last_client = ClientClient.objects.order_by('-future_client_number').first()
        
        if last_client and last_client.future_client_number and last_client.future_client_number.startswith('FUT'):
            # Extract number, increment it
            last_number_str = last_client.future_client_number[3:] # e.g., '00001'
            last_number = int(last_number_str)
            next_number = last_number + 1
            
            # Format back to 'FUT' + padded number (e.g., 'FUT00002')
            return f"FUT{next_number:05d}"
        
    except Exception as e:
        # If table is empty or format fails, start at 1
        print(f"Error generating client number: {e}")
        pass

    return "FUT00001"


# --- Date Conversion Helper Function ---
def safe_parse_date(date_string):
    """Parses DD/MM/YYYY to YYYY-MM-DD format or returns None if empty/invalid."""
    if not date_string:
        return None
    try:
        # Input format from HTML is DD/MM/YYYY
        # Output format required by Django DateField is YYYY-MM-DD
        return datetime.strptime(date_string, '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
        # If parsing fails (e.g., invalid date or wrong format)
        return None
# ------------------------------------------------------


# --- Helper Function for Parsing Repeating Data ---

def parse_repeating_data(request_data, prefix, field_names):
    """
    Parses dynamic, repeating form data (e.g., directors, contacts) 
    by checking for indexed field names (e.g., 'dir_name_0', 'dir_name_1').
    """
    data = request_data.POST
    files = request_data.FILES if hasattr(request_data, 'FILES') and request_data.FILES else {}
    
    entities = []
    index = 0
    while True:
        if prefix == 'contact':
            name_key = f'{prefix}-name-{index}'
        elif prefix in ('dir', 'owner'):
            name_key = f'{prefix}_name_{index}'
        else:
            name_key = f'{prefix}_name_{index}'

        if index > 0 and (name_key not in data or not data.get(name_key)):
              break
        
        if prefix in ('dir', 'owner') and index == 0:
            if not data.get(f'{prefix}_name_0'):
                  break
        
        if index > 100: 
            break
        
        entity_data = {}
        found_entity = False

        for field in field_names:
            if prefix == 'contact':
                key = f'{prefix}-{field}-{index}' 
            else:
                key = f'{prefix}_{field}_{index}'
            
            value = data.get(key)
            
            if 'postal_check' in field or field.endswith('_q'):
                if 'check' in field:
                    entity_data[field] = (value == 'on')
                elif '_q' in field:
                    entity_data[field] = (value == 'Yes')
            elif field.endswith('_file'):
                file_key = f'{prefix}_{field}_{index}' if index > 0 else field
                file_obj = files.get(file_key) 
                entity_data[field] = file_obj.name if file_obj else None
                if file_obj:
                    found_entity = True
            else:
                entity_data[field] = value
                
            if value:
                found_entity = True
                
        if found_entity:
            entity_data['index'] = index
            entities.append(entity_data)

        index += 1
    
    return entities


# --- Core Client Views (Now DB-driven) ---

def home_view(request):
    """Renders the dashboard/home page, relying on the database."""
    return render(request, 'consulting/home.html', {})


def consulting_home(request):
    """Renders the 'home.html' template."""
    return render(request, 'consulting/home.html', {})

def client_list_view(request):
    """Renders the client list page by fetching all clients from the database."""
    clients = ClientClient.objects.all().order_by('client_name')
    context = {
        'clients': clients
    }
    return render(request, 'consulting/client_list.html', context)


def client_info_view(request, client_code):
    """This view renders the detail page for a single client, fetching ALL related FICA data."""
    client = get_object_or_404(ClientClient, future_client_number=client_code)
    
    client_contacts = ClientContact.objects.filter(client=client).order_by('id')
    fica_addresses = FicaAddress.objects.filter(client=client).order_by('id')
    fica_resp_person = FicaResponsiblePerson.objects.filter(client=client).order_by('id')
    fica_directors = FicaDirector.objects.filter(client=client).order_by('id')
    fica_owners = FicaBeneficialOwner.objects.filter(client=client).order_by('id')
    
    physical_addr = fica_addresses.filter(address_type='physical').first()
    postal_addr = fica_addresses.filter(address_type='postal').first()

    date_added_formatted = client.date_added.strftime('%d/%m/%Y') if client.date_added else ''
    declaration_date_formatted = client.declaration_date.strftime('%d/%m/%Y') if client.declaration_date else ''


    context = {
        'client': client,
        'client_contacts': client_contacts,
        'physical_addr': physical_addr,
        'postal_addr': postal_addr,
        'fica_resp_person': fica_resp_person, 
        'fica_directors': fica_directors,
        'fica_owners': fica_owners,
        'date_added_formatted': date_added_formatted,
        'declaration_date_formatted': declaration_date_formatted,
    }
    
    return render(request, 'consulting/client_info.html', context)


# --- EDIT CLIENT VIEW ---
@require_http_methods(["GET", "POST"])
def edit_client_view(request, client_code):
    """Handles rendering the edit form (GET) with existing data and saving updates (POST)."""
    client = get_object_or_404(ClientClient, future_client_number=client_code)
    
    client_contacts = ClientContact.objects.filter(client=client).order_by('id')
    fica_addresses = FicaAddress.objects.filter(client=client).order_by('id')
    fica_resp_person = FicaResponsiblePerson.objects.filter(client=client).order_by('id')
    fica_directors = FicaDirector.objects.filter(client=client).order_by('id')
    fica_owners = FicaBeneficialOwner.objects.filter(client=client).order_by('id')
    
    physical_addr = fica_addresses.filter(address_type='physical').first()
    postal_addr = fica_addresses.filter(address_type='postal').first()

    if request.method == 'POST':
        data = request.POST
        files = request.FILES if request.FILES else {}

        try:
            with transaction.atomic():
                # --- 1. UPDATE ClientClient (Core Data + Client Name + Step 7 + Docs) ---
                
                date_added = safe_parse_date(data.get('date'))
                declaration_date_formatted = safe_parse_date(data.get('declaration_date'))
                
                def get_file_name(field_name):
                    file_obj = files.get(field_name)
                    return file_obj.name if file_obj else None

                # Update ClientClient instance fields directly
                client.client_name = data.get('client_name', client.client_name)
                client.consultant = data.get('consultant', client.consultant)
                client.industry = data.get('industry', client.industry)
                client.status = data.get('status', client.status)
                client.date_added = date_added
                client.years_active = data.get('years', client.years_active)
                client.employees = data.get('employees', client.employees)

                client.product = data.get('product', client.product)
                client.third_party_contract = (data.get('third_party_contract') == 'yes')
                client.third_party_contact = data.get('third_party_contact', client.third_party_contact)
                client.administrator = data.get('administrator', client.administrator)
                client.umbrella_fund = data.get('umbrella_fund', client.umbrella_fund)
                client.insurer = data.get('insurer', client.insurer)
                client.assets = data.get('assets', client.assets)

                # Document Statuses (for Tab 1) - update status and file name if a NEW file is uploaded
                client.consulting_letter_status = (data.get('consulting_letter') == 'yes')
                if get_file_name('consulting_letter_file'): client.consulting_letter_file = get_file_name('consulting_letter_file')
                
                client.sla_status = (data.get('sla') == 'yes')
                if get_file_name('sla_file'): client.sla_file = get_file_name('sla_file')
                
                client.third_party_doc_status = (data.get('third_party_doc') == 'yes')
                if get_file_name('third_party_doc_file'): client.third_party_doc_file = get_file_name('third_party_doc_file')
                
                # Step 7 updates
                client.nature_of_relationship = data.get('nat_rel', client.nature_of_relationship)
                client.purpose_of_relationship = data.get('purp_rel', client.purpose_of_relationship)
                client.source_of_funds = data.get('source_funds', client.source_of_funds)
                client.due_diligence_form_name = data.get('due_diligence_form_name', client.due_diligence_form_name)
                client.declaration_name = data.get('declaration_name', client.declaration_name)
                client.declaration_delegation = data.get('declaration_delegation', client.declaration_delegation)
                client.declaration_date = declaration_date_formatted
                if get_file_name('signed_form_upload'): client.signed_form_upload = get_file_name('signed_form_upload')
                
                client.save() 

                # --- 2. UPDATE/CREATE FicaAddress (Company Physical & Postal - Step 2) ---
                if physical_addr:
                    physical_addr.line1 = data.get('physical_line1', physical_addr.line1)
                    physical_addr.line2 = data.get('physical_line2', physical_addr.line2)
                    physical_addr.province = data.get('physical_province', physical_addr.province)
                    physical_addr.city = data.get('physical_city', physical_addr.city)
                    physical_addr.suburb = data.get('physical_suburb', physical_addr.suburb)
                    physical_addr.postal_code = data.get('physical_code', physical_addr.postal_code)
                    physical_addr.save()
                else:
                     FicaAddress.objects.create(client=client, address_type='physical', line1=data.get('physical_line1'))

                is_same_as_physical = (data.get('same_as_physical') == 'on')
                
                if is_same_as_physical and postal_addr:
                    postal_addr.delete()
                elif not is_same_as_physical:
                    if postal_addr:
                        postal_addr.line1 = data.get('postal_line1', postal_addr.line1)
                        postal_addr.line2 = data.get('postal_line2', postal_addr.line2)
                        postal_addr.province = data.get('postal_province', postal_addr.province)
                        postal_addr.city = data.get('postal_city', postal_addr.city)
                        postal_addr.suburb = data.get('postal_suburb', postal_addr.suburb)
                        postal_addr.postal_code = data.get('postal_code', postal_addr.postal_code)
                        postal_addr.save()
                    else:
                        FicaAddress.objects.create(
                            client=client,
                            address_type='postal',
                            line1=data.get('postal_line1'),
                            line2=data.get('postal_line2'),
                            province=data.get('postal_province'),
                            city=data.get('postal_city'),
                            suburb=data.get('postal_suburb'),
                            postal_code=data.get('postal_code'),
                        )

                # --- 3. Manage ClientContact (Tab 2) ---
                ClientContact.objects.filter(client=client).delete()
                contact_field_names = ['name', 'surname', 'job_title', 'landline', 'cell', 'email', 'physical', 'postal', 'city', 'province', 'birthday', 'notes', 'interests']
                contacts = parse_repeating_data(request, 'contact', contact_field_names) 
                for contact_data in contacts:
                    ClientContact.objects.create(
                        client=client,
                        name=contact_data.get('name'), surname=contact_data.get('surname'),
                        job_title=contact_data.get('job_title'), landline=contact_data.get('landline'),
                        cell_no=contact_data.get('cell'), email=contact_data.get('email'),
                        physical_address=contact_data.get('physical'), postal_address=contact_data.get('postal'),
                        city_town=contact_data.get('city'), province=contact_data.get('province'),
                        birthday=contact_data.get('birthday'), notes=contact_data.get('notes'),
                        interests=contact_data.get('interests'),
                    )


                # --- 4. Manage FicaResponsiblePerson (Step 4) ---
                FicaResponsiblePerson.objects.filter(client=client).delete()
                if data.get('resp_name'):
                     FicaResponsiblePerson.objects.create(
                         client=client, 
                         name=data.get('resp_name'), surname=data.get('resp_surname'),
                         designation=data.get('resp_designation'), id_number=data.get('resp_id'),
                         contact_number=data.get('resp_contact'), email_address=data.get('resp_email'),
                         resp_line1=data.get('resp_line1'), resp_line2=data.get('resp_line2'),
                         resp_province=data.get('resp_province'), resp_city=data.get('resp_city'),
                         resp_suburb=data.get('resp_suburb'), resp_code=data.get('resp_code'),
                         circular_upload_file=get_file_name('circular_upload'),
                         doc_signed_upload_file=get_file_name('doc_signed_upload'),
                     )
                
                # --- 5. Manage FicaDirector (Step 5) ---
                FicaDirector.objects.filter(client=client).delete()
                dir_fields = ['name', 'surname', 'designation', 'id', 'contact', 'email', 
                    'phys_line1', 'phys_line2', 'phys_province', 'phys_city', 'phys_suburb', 'phys_code', 
                    'postal_check', 'postal_line1', 'postal_line2', 'postal_province',
                    'proof_addr_file', 'id_copy_file',
                    'pep_q', 'pep_reason', 'pip_q', 'pip_reason', 'ppo_q', 'ppo_reason', 'kca_q', 'kca_reason']
                
                directors = parse_repeating_data(request, 'dir', dir_fields)
                for director_data in directors:
                    director_index = director_data.get("index")

                    FicaDirector.objects.create(
                        client=client, 
                        name=director_data.get('name'), surname=director_data.get('surname'),
                        designation=director_data.get('designation'), id_number=director_data.get('id'),
                        contact_number=director_data.get('contact'), email_address=director_data.get('email'),
                        phys_line1=director_data.get('phys_line1'), phys_line2=director_data.get('phys_line2'),
                        phys_province=director_data.get('phys_province'), phys_city=director_data.get('phys_city'),
                        phys_suburb=director_data.get('phys_suburb'), phys_code=director_data.get('phys_code'),
                        postal_same_as_phys=director_data.get('postal_check'),
                        postal_line1=director_data.get('postal_line1'), postal_line2=director_data.get('postal_line2'),
                        postal_province=director_data.get('postal_province'),
                        proof_addr_file=get_file_name(f'dir_proof_addr_{director_index}'),
                        id_copy_file=get_file_name(f'dir_id_copy_{director_index}'),
                        is_pep=director_data.get('pep_q'), pep_reason=director_data.get('pep_reason'),
                        is_pip=director_data.get('pip_q'), pip_reason=director_data.get('pip_reason'),
                        is_ppo=director_data.get('ppo_q'), ppo_reason=director_data.get('ppo_reason'),
                        is_kca=director_data.get('kca_q'), kca_reason=director_data.get('kca_reason'),
                    )


                # --- 6. Manage FicaBeneficialOwner (Step 6) ---
                FicaBeneficialOwner.objects.filter(client=client).delete()
                owner_fields = ['name', 'surname', 'designation', 'id', 'contact', 'email', 
                    'phys_line1', 'phys_line2', 'phys_province', 'phys_city', 'phys_suburb', 'phys_code', 
                    'postal_check', 'postal_line1', 'postal_line2', 'postal_province',
                    'proof_addr_file', 'id_copy_file',
                    'pep_q', 'pep_reason', 'pip_q', 'pip_reason', 'ppo_q', 'ppo_reason', 'kca_q', 'kca_reason']
                
                owners = parse_repeating_data(request, 'owner', owner_fields)
                for owner_data in owners:
                    owner_index = owner_data.get("index")

                    FicaBeneficialOwner.objects.create(
                        client=client, 
                        name=owner_data.get('name'), surname=owner_data.get('surname'),
                        designation=owner_data.get('designation'), id_number=owner_data.get('id'),
                        contact_number=owner_data.get('contact'), email_address=owner_data.get('email'),
                        phys_line1=owner_data.get('phys_line1'), phys_line2=owner_data.get('phys_line2'),
                        phys_province=owner_data.get('phys_province'), phys_city=owner_data.get('phys_city'),
                        phys_suburb=owner_data.get('phys_suburb'), phys_code=owner_data.get('phys_code'),
                        postal_same_as_phys=owner_data.get('postal_check'),
                        postal_line1=owner_data.get('postal_line1'), postal_line2=owner_data.get('postal_line2'),
                        postal_province=owner_data.get('postal_province'),
                        proof_addr_file=get_file_name(f'owner_proof_addr_{owner_index}'),
                        id_copy_file=get_file_name(f'owner_id_copy_{owner_index}'),
                        is_pep=owner_data.get('pep_q'), pep_reason=owner_data.get('pep_reason'),
                        is_pip=owner_data.get('pip_q'), pip_reason=owner_data.get('pip_reason'),
                        is_ppo=owner_data.get('ppo_q'), ppo_reason=owner_data.get('ppo_reason'),
                        is_kca=owner_data.get('kca_q'), kca_reason=owner_data.get('kca_reason'),
                    )


            messages.success(request, f"Client {client.future_client_number} updated successfully!")
            return redirect('client_info', client_code=client_code) 

        except Exception as e:
            error_msg = f"Error saving client updates. Please ensure all required fields are filled out. Database error: {e}"
            print(f"FATAL ERROR ON SAVE: {e}")
            messages.error(request, error_msg)
            
    context = {
        'client': client,
        'client_contacts': client_contacts,
        'physical_addr': physical_addr,
        'postal_addr': postal_addr,
        'fica_resp_person': fica_resp_person.first(), 
        'fica_directors': fica_directors,
        'fica_owners': fica_owners,
        'date_added_formatted': client.date_added.strftime('%d/%m/%Y') if client.date_added else '',
        'declaration_date_formatted': client.declaration_date.strftime('%d/%m/%Y') if client.declaration_date else '',
    }
    return render(request, 'consulting/edit_client.html', context)


# --- ADD CLIENT VIEW ---

@require_http_methods(["GET", "POST"])
def add_client_view(request):
    """Handles rendering the form (GET) and saving all client and FICA data (POST)."""
    if request.method == 'POST':
        data = request.POST
        files = request.FILES if request.FILES else {}
        client = None
        client_code = data.get('client_number', 'N/A')

        try:
            with transaction.atomic():
                
                # --- 1. Save ClientClient (Core Data + Client Name + Step 7 + Docs) ---
                
                date_added = safe_parse_date(data.get('date'))
                declaration_date_formatted = safe_parse_date(data.get('declaration_date'))
                
                def get_file_name(field_name):
                    file_obj = files.get(field_name)
                    return file_obj.name if file_obj else None

                client = ClientClient.objects.create(
                    future_client_number=client_code, 
                    client_name=data.get('client_name', 'N/A'),
                    consultant=data.get('consultant', 'N/A'),
                    industry=data.get('industry'),
                    status=data.get('status', 'N/A'),
                    date_added=date_added, 
                    years_active=data.get('years'),
                    employees=data.get('employees'),

                    product=data.get('product'),
                    third_party_contract=(data.get('third_party_contract') == 'yes'),
                    third_party_contact=data.get('third_party_contact'),
                    administrator=data.get('administrator'),
                    umbrella_fund=data.get('umbrella_fund'),
                    insurer=data.get('insurer'),
                    assets=data.get('assets'),

                    consulting_letter_status=(data.get('consulting_letter') == 'yes'),
                    consulting_letter_file=get_file_name('consulting_letter_file'),
                    sla_status=(data.get('sla') == 'yes'),
                    sla_file=get_file_name('sla_file'),
                    third_party_doc_status=(data.get('third_party_doc') == 'yes'),
                    third_party_doc_file=get_file_name('third_party_doc_file'),

                    # Step 7: Transaction Information & Declaration
                    nature_of_relationship=data.get('nat_rel'),
                    purpose_of_relationship=data.get('purp_rel'),
                    source_of_funds=data.get('source_funds'),
                    due_diligence_form_name=data.get('due_diligence_form_name'),
                    declaration_name=data.get('declaration_name'),
                    declaration_delegation=data.get('declaration_delegation'),
                    declaration_date=declaration_date_formatted, 
                    signed_form_upload=get_file_name('signed_form_upload'),
                )

                # --- 2. Save FicaAddress (Company Physical & Postal - Step 2) ---
                FicaAddress.objects.create(
                    client=client,
                    address_type='physical',
                    line1=data.get('physical_line1'),
                    line2=data.get('physical_line2'),
                    province=data.get('physical_province'),
                    city=data.get('physical_city'),
                    suburb=data.get('physical_suburb'),
                    postal_code=data.get('physical_code'),
                )
                
                if data.get('same_as_physical') != 'on':
                    FicaAddress.objects.create(
                        client=client,
                        address_type='postal',
                        line1=data.get('postal_line1'),
                        line2=data.get('postal_line2'),
                        province=data.get('postal_province'),
                        city=data.get('postal_city'),
                        suburb=data.get('postal_suburb'),
                        postal_code=data.get('postal_code'),
                    )

                # --- 3. Save ClientContact (Tab 2) ---
                contact_field_names = ['name', 'surname', 'job_title', 'landline', 'cell', 'email', 'physical', 'postal', 'city', 'province', 'birthday', 'notes', 'interests']
                contacts = parse_repeating_data(request, 'contact', contact_field_names) 
                for contact_data in contacts:
                    ClientContact.objects.create(
                        client=client,
                        name=contact_data.get('name'), surname=contact_data.get('surname'),
                        job_title=contact_data.get('job_title'), landline=contact_data.get('landline'),
                        cell_no=contact_data.get('cell'), email=contact_data.get('email'),
                        physical_address=contact_data.get('physical'), postal_address=contact_data.get('postal'),
                        city_town=contact_data.get('city'), province=contact_data.get('province'),
                        birthday=contact_data.get('birthday'), notes=contact_data.get('notes'),
                        interests=contact_data.get('interests'),
                    )


                # --- 4. Save FicaResponsiblePerson (Step 4) ---
                if data.get('resp_name'):
                     FicaResponsiblePerson.objects.create(
                         client=client, 
                         name=data.get('resp_name'), surname=data.get('resp_surname'),
                         designation=data.get('resp_designation'), id_number=data.get('resp_id'),
                         contact_number=data.get('resp_contact'), email_address=data.get('resp_email'),
                         resp_line1=data.get('resp_line1'), resp_line2=data.get('resp_line2'),
                         resp_province=data.get('resp_province'), resp_city=data.get('resp_city'),
                         resp_suburb=data.get('resp_suburb'), resp_code=data.get('resp_code'),
                         circular_upload_file=get_file_name('circular_upload'),
                         doc_signed_upload_file=get_file_name('doc_signed_upload'),
                     )
                
                # --- 5. Save FicaDirector (Step 5) ---
                dir_fields = ['name', 'surname', 'designation', 'id', 'contact', 'email', 
                    'phys_line1', 'phys_line2', 'phys_province', 'phys_city', 'phys_suburb', 'phys_code', 
                    'postal_check', 'postal_line1', 'postal_line2', 'postal_province',
                    'proof_addr_file', 'id_copy_file',
                    'pep_q', 'pep_reason', 'pip_q', 'pip_reason', 'ppo_q', 'ppo_reason', 'kca_q', 'kca_reason']
                
                directors = parse_repeating_data(request, 'dir', dir_fields)
                for director_data in directors:
                    director_index = director_data.get("index")

                    FicaDirector.objects.create(
                        client=client, 
                        name=director_data.get('name'), surname=director_data.get('surname'),
                        designation=director_data.get('designation'), id_number=director_data.get('id'),
                        contact_number=director_data.get('contact'), email_address=director_data.get('email'),
                        phys_line1=director_data.get('phys_line1'), phys_line2=director_data.get('phys_line2'),
                        phys_province=director_data.get('phys_province'), phys_city=director_data.get('phys_city'),
                        phys_suburb=director_data.get('phys_suburb'), phys_code=director_data.get('phys_code'),
                        postal_same_as_phys=director_data.get('postal_check'),
                        postal_line1=director_data.get('postal_line1'), postal_line2=director_data.get('postal_line2'),
                        postal_province=director_data.get('postal_province'),
                        proof_addr_file=get_file_name(f'dir_proof_addr_{director_index}'),
                        id_copy_file=get_file_name(f'dir_id_copy_{director_index}'),
                        is_pep=director_data.get('pep_q'), pep_reason=director_data.get('pep_reason'),
                        is_pip=director_data.get('pip_q'), pip_reason=director_data.get('pip_reason'),
                        is_ppo=director_data.get('ppo_q'), ppo_reason=director_data.get('ppo_reason'),
                        is_kca=director_data.get('kca_q'), kca_reason=director_data.get('kca_reason'),
                    )


                # --- 6. Save FicaBeneficialOwner (Step 6) ---
                owner_fields = ['name', 'surname', 'designation', 'id', 'contact', 'email', 
                    'phys_line1', 'phys_line2', 'phys_province', 'phys_city', 'phys_suburb', 'phys_code', 
                    'postal_check', 'postal_line1', 'postal_line2', 'postal_province',
                    'proof_addr_file', 'id_copy_file',
                    'pep_q', 'pep_reason', 'pip_q', 'pip_reason', 'ppo_q', 'ppo_reason', 'kca_q', 'kca_reason']
                
                owners = parse_repeating_data(request, 'owner', owner_fields)
                for owner_data in owners:
                    owner_index = owner_data.get("index")

                    FicaBeneficialOwner.objects.create(
                        client=client, 
                        name=owner_data.get('name'), surname=owner_data.get('surname'),
                        designation=owner_data.get('designation'), id_number=owner_data.get('id'),
                        contact_number=owner_data.get('contact'), email_address=owner_data.get('email'),
                        phys_line1=owner_data.get('phys_line1'), phys_line2=owner_data.get('phys_line2'),
                        phys_province=owner_data.get('phys_province'), phys_city=owner_data.get('phys_city'),
                        phys_suburb=owner_data.get('phys_suburb'), phys_code=owner_data.get('phys_code'),
                        postal_same_as_phys=owner_data.get('postal_check'),
                        postal_line1=owner_data.get('postal_line1'), postal_line2=owner_data.get('postal_line2'),
                        postal_province=owner_data.get('postal_province'),
                        proof_addr_file=get_file_name(f'owner_proof_addr_{owner_index}'),
                        id_copy_file=get_file_name(f'owner_id_copy_{owner_index}'),
                        is_pep=owner_data.get('pep_q'), pep_reason=owner_data.get('pep_reason'),
                        is_pip=owner_data.get('pip_q'), pip_reason=owner_data.get('pip_reason'),
                        is_ppo=owner_data.get('ppo_q'), ppo_reason=owner_data.get('ppo_reason'),
                        is_kca=owner_data.get('kca_q'), kca_reason=owner_data.get('kca_reason'),
                    )


            messages.success(request, f"New Client {client.future_client_number} added successfully! Redirecting to client profile.")
            return redirect('client_info', client_code=client_code) 

        except Exception as e:
            error_msg = f"Error saving client. Please ensure all required fields are filled out. Database error: {e}"
            print(f"FATAL ERROR ON SAVE: {e}")
            messages.error(request, error_msg)
            
    next_client_number = get_next_client_number()
    context = {'client_number': next_client_number}
    return render(request, 'consulting/add_new_client.html', context)
    
# --- LEAD VIEWS (Now DB-driven) ---

@csrf_exempt 
@require_http_methods(["POST"])
def log_lead_note_view(request, lead_id):
    """
    Handles the form submission to log a new note. 
    It updates the Lead's communication_type, note_type, last_follow_up date, 
    and appends a structured log entry to the internal_notes field.
    """
    lead = get_object_or_404(Lead, pk=lead_id)

    try:
        if not request.POST:
            messages.error(request, "No form data received.")
            return redirect(f'/leads/{lead_id}/info/#tab2')
            
        with transaction.atomic():
            
            # --- 1. Capture and format new note entry ---
            communication_type_new = request.POST.get('communication_type', 'N/A')
            note_type_new = request.POST.get('note_category', 'N/A')
            note_selection = request.POST.get('note_selection', 'N/A')
            note_content = request.POST.get('note_content', 'No content entered.')
            
            if not note_content or note_content == 'No content entered.':
                 messages.error(request, "Note content cannot be empty. Please enter details.")
                 return redirect(f'/leads/{lead_id}/info/#tab2')
            
            # Identify the user/poster 
            poster = lead.assigned_to or 'Unassigned Consultant' 
            timestamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M')

            # Create a clear, visible log entry string, ready to be appended to internal_notes
            new_note_entry = (
                f"\n\n--- LOGGED: {timestamp} ---\n"
                f"COMM TYPE: {communication_type_new.replace('_', ' ').title()}\n"
                f"NOTE TYPE: {note_type_new.replace('_', ' ').title()}\n"
                f"SELECTION: {note_selection or 'N/A'}\n"
                f"POSTED BY: {poster}\n"
                f"NOTES:\n{note_content}"
            )

            # Update the Lead's fields with the LATEST communication details
            lead.communication_type = communication_type_new
            lead.note_type = note_type_new
            
            # Append the new note to the internal_notes history
            current_notes = lead.internal_notes or ""
            lead.internal_notes = current_notes + new_note_entry

            # Update the Lead's last_follow_up date to today
            lead.last_follow_up = dt.date.today()
            lead.save()

            messages.success(request, "Communication successfully logged and Lead follow-up date updated.")
            
    except Exception as e:
        messages.error(request, f"Error logging communication. Database error: {e}")
        print(f"ERROR LOGGING LEAD NOTE: {e}")

    # Redirect back to the lead info page, staying on the Notes tab
    return redirect(f'/leads/{lead_id}/info/#tab2')


@csrf_exempt 
def add_new_lead_view(request):
    """
    Handles displaying the Add New Lead form (GET) and processing submission (POST).
    """
    
    consultant_options = ['AWIE DE SWARDT', 'MARIDA BOTHA', 'STEPHAN DE WAAL', 'MERRIL FENNESSY', 'Unassigned']
    product_options = ['Retirement Fund', 'Health Care', 'Individual Client', 'SLA Services', 'Umbrella Fund', 'Other']

    if request.method == 'POST':
        
        try:
            date_received_str = request.POST.get('date_received')
            date_received = dt.datetime.strptime(date_received_str, '%Y-%m-%d').date()
        except Exception:
            context = {
                'error_message': 'Invalid date format. Please use YYYY-MM-DD.',
                'consultant_options': consultant_options,
                'product_options': product_options,
                'current_date': dt.date.today().strftime('%Y-%m-%d')
            }
            return render(request, 'consulting/add_new_lead.html', context)

        try:
            Lead.objects.create(
                lead_received_from=request.POST['lead_received_from'],
                date_received=date_received,
                company_name=request.POST['company_name'],
                contact_person=request.POST['contact_person'],
                contact_number=request.POST.get('contact_number', ''),
                contact_email=request.POST.get('contact_email', ''),
                product_required=request.POST['product_required'],
                status='New', 
                assigned_to=request.POST.get('assigned_to', 'Unassigned'),
                last_follow_up=date_received, 
                internal_notes=request.POST.get('internal_notes', ''),
                communication_type=None, 
                note_type=None,
            )
        except Exception as e:
            context = {
                'error_message': f'Error saving lead to database: {e}',
                'consultant_options': consultant_options,
                'product_options': product_options,
                'current_date': dt.date.today().strftime('%Y-%m-%d')
            }
            print(f"Database error on lead creation: {e}")
            return render(request, 'consulting/add_new_lead.html', context)
        
        return redirect('lead_list')

    context = {
        'consultant_options': consultant_options,
        'product_options': product_options,
        'current_date': dt.date.today().strftime('%Y-%m-%d')
    }
    return render(request, 'consulting/add_new_lead.html', context)


def lead_list_view(request):
    """Displays the list of New Leads by querying the database."""
    
    leads_list = list(Lead.objects.all()) # Fetching leads from the database
    
    # --- Sorting Logic (now runs on live data) ---
    sort_by = request.GET.get('sort', '-date_received')
    
    def get_sort_key(lead):
        default_date = dt.date(dt.MINYEAR, 1, 1)

        if 'last_follow_up' in sort_by:
            return getattr(lead, 'last_follow_up', None) or default_date
        
        return getattr(lead, 'date_received', default_date)

    reverse_sort = sort_by.startswith('-') or sort_by.endswith('_desc')

    leads_list.sort(key=get_sort_key, reverse=reverse_sort)
    
    context = {
        'leads': leads_list,
        'current_sort': sort_by,
        'consultant_options': ['AWIE DE SWARDT', 'MARIDA BOTHA', 'STEPHAN DE WAAL', 'MERRIL FENNESSY'],
        'product_options': ['Retirement Fund', 'Health Care', 'Individual Client', 'SLA Services', 'Umbrella Fund'],
    }
    
    return render(request, 'consulting/lead_list.html', context)


def lead_info_view(request, lead_id):
    """
    Displays the details of a single lead by querying the database.
    """
    lead = get_object_or_404(Lead, pk=lead_id)
    
    context = {
        'lead': lead,
    }
    
    return render(request, 'consulting/lead_info.html', context)


@require_http_methods(["GET", "POST"])
def lead_edit_view(request, lead_id):
    """
    View for lead editing/qualification form. 
    Handles displaying the editable form and processing POST requests to update lead data.
    """
    lead = get_object_or_404(Lead, pk=lead_id)

    # --- Configuration (required for template rendering) ---
    consultant_options = ['AWIE DE SWARDT', 'MARIDA BOTHA', 'STEPHAN DE WAAL', 'MERRIL FENNESSY', 'Unassigned']
    product_options = ['Retirement Fund', 'Health Care', 'Individual Client', 'SLA Services', 'Umbrella Fund', 'Other']
    status_options = ['New', 'In-Progress', 'Taken Up', 'Not Taken Up', 'Parked']

    # Helper for converting YYYY-MM-DD input string back to date object
    def clean_date_input(date_str):
        if not date_str: return None
        try:
            return dt.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None

    if request.method == 'POST':
        data = request.POST
        
        try:
            with transaction.atomic():
                lead.company_name = data.get('company_name', lead.company_name)
                lead.lead_received_from = data.get('lead_received_from', lead.lead_received_from)
                
                # Update date fields
                lead.date_received = clean_date_input(data.get('date_received'))
                lead.date_accepted = clean_date_input(data.get('date_accepted'))
                lead.start_date = clean_date_input(data.get('start_date'))

                lead.contact_person = data.get('contact_person', lead.contact_person)
                lead.contact_number = data.get('contact_number', lead.contact_number)
                lead.contact_email = data.get('contact_email', lead.contact_email)
                lead.product_required = data.get('product_required', lead.product_required)
                lead.assigned_to = data.get('assigned_to', lead.assigned_to)
                lead.status = data.get('status', lead.status)
                
                lead.save()
            
            messages.success(request, f"Lead {lead.company_name} updated successfully!")
            # Redirect back to the read-only info page after saving
            return redirect('lead_info', lead_id=lead.id)

        except Exception as e:
            error_msg = f"Error saving lead updates: {e}"
            print(f"ERROR EDITING LEAD: {e}")
            messages.error(request, error_msg)
            
    # Prepare context for GET request (or failed POST)
    context = {
        'lead': lead,
        'consultant_options': consultant_options,
        'product_options': product_options,
        'status_options': status_options,
        # Format existing dates to YYYY-MM-DD string for HTML <input type="date">
        'date_received_str': lead.date_received.strftime('%Y-%m-%d') if lead.date_received else '',
        'date_accepted_str': lead.date_accepted.strftime('%Y-%m-%d') if lead.date_accepted else '',
        'start_date_str': lead.start_date.strftime('%Y-%m-%d') if lead.start_date else '',
    }
    # Render the dedicated edit form template
    return render(request, 'consulting/edit_lead_info.html', context)

# Assuming your models.py is located in the same directory (myapp)
from .models import Claims, ClaimsNotes # <-- Import the new model!
from django.utils import timezone # <-- CORRECTED: Use Django's timezone utility
# --- Constants (matching frontend dropdowns) ---
CONSULTANTS = [
    'Awie de Swardt',
    'Marika Botha',
    'Stephan de Waal',
    'Merri Fennesy'
]

CLAIM_TYPES = [
    'Funeral - main member',
    'Funeral - spouse',
    'Funeral - child',
    'Funeral - family',
    'Normal Withdrawal',
    'Divorce',
    'Disability',
    'Temporary Disability',
    'Death',
    'Retirement'
]

INSURERS = [ 
    'Sanlam',
    'Momentum',
    'Old Mutual',
    'Hollard',
    'Triarc',
    'Acravest',
    'Liberty Life',
    'Alan Gray',
    'TSA'
]
# -----------------------------------


def claims_dashboard(request):
    """
    Fetches all claims and their related notes, serializes them to JSON for 
    client-side detail lookup, and renders the claims dashboard.
    """
    claims_queryset = Claims.objects.all().order_by('-created_date') 
    
    # --- Fetch all notes once, indexed by claim_id ---
    all_notes = ClaimsNotes.objects.all().order_by('-created_at')
    notes_by_claim = {}
    
    for note in all_notes:
        note_data = {
            'title': f"{note.note_selection} ({note.communication_type})",
            'body': note.note_body,
            'createdBy': note.created_by,
            'date': note.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        if note.claim_id not in notes_by_claim:
            notes_by_claim[note.claim_id] = []
        notes_by_claim[note.claim_id].append(note_data)
        
    # --- Serialization for Client-Side Detail Lookup ---
    claims_list = []
    for claim in claims_queryset:
        claims_list.append({
            'id': claim.id,
            'memberNo': claim.member_no,
            'firstName': claim.first_name,
            'surname': claim.surname,
            'idPassport': claim.id_passport,
            'employerCode': claim.employer_code,
            'employerName': claim.employer_name,
            'insurer': claim.insurer,
            'claimType': claim.claim_type,
            'consultant': claim.consultant,
            'lastAction': claim.last_action,
            'status': claim.status,
            'createdDate': claim.created_date.strftime("%Y-%m-%d") if claim.created_date else '',
            'initialNotes': claim.initial_notes or '',
            'notes': notes_by_claim.get(claim.id, []) # <-- INCLUDE NOTES HERE
        })
        
    claims_json = json.dumps(claims_list)

    context = {
        'claims': claims_queryset,
        'claims_json': claims_json, 
        'consultants': CONSULTANTS,
        'claim_types': CLAIM_TYPES,
        'insurers': INSURERS, 
        'active_tab': 'Claims' 
    }
    return render(request, 'consulting/claims_dashboard.html', context)


@require_http_methods(["POST"])
def create_new_claim(request):
    """
    Handles the submission of a new claim record.
    (Existing function, unchanged logic)
    """
    try:
        member_no = request.POST.get('new_member_no')
        first_name = request.POST.get('new_first_name')
        surname = request.POST.get('new_surname')
        id_passport = request.POST.get('new_id_passport')
        employer_code = request.POST.get('new_employer_code')
        employer_name = request.POST.get('new_employer_name')
        insurer = request.POST.get('new_insurer')
        claim_type = request.POST.get('new_claim_type')
        consultant = request.POST.get('new_consultant')
        initial_notes = request.POST.get('new_notes', '')

        if not all([member_no, first_name, surname, id_passport, employer_code, employer_name, insurer, claim_type, consultant]):
            print("ERROR: Missing required fields in claim submission.")
            return redirect(reverse('claims_dashboard'))

        Claims.objects.create(
            member_no=member_no,
            first_name=first_name,
            surname=surname,
            id_passport=id_passport,
            employer_code=employer_code,
            employer_name=employer_name,
            insurer=insurer,
            claim_type=claim_type,
            consultant=consultant,
            initial_notes=initial_notes,
            created_date=date.today()
        )
        
        return redirect(reverse('claims_dashboard'))

    except IntegrityError as e:
        print(f"Database Integrity Error: {e}")
        return redirect(reverse('claims_dashboard'))
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return redirect(reverse('claims_dashboard'))


@require_http_methods(["POST"])
def create_claim_note(request):
    """
    Handles the submission of a new ClaimsNotes record from the detail popup.
    """
    try:
        # Get data from the hidden form fields
        claim_id = request.POST.get('note_claim_id')
        comm_type = request.POST.get('note_comm_type')
        selection = request.POST.get('note_selection')
        body = request.POST.get('note_body')

        # Basic validation
        if not all([claim_id, comm_type, selection, body]):
            print("ERROR: Missing required fields for note submission.")
            return redirect(reverse('claims_dashboard'))

        # Fetch the related Claim object
        try:
            claim = Claims.objects.get(pk=claim_id)
        except Claims.DoesNotExist:
            print(f"ERROR: Claim with ID {claim_id} not found.")
            return redirect(reverse('claims_dashboard'))
            
        # NOTE: In a real environment, request.user.username would be used here.
        # Assuming a placeholder for created_by since user context isn't defined.
        created_by_user = request.user.username if request.user.is_authenticated else "System User"

        # Create the new ClaimsNotes object (using the unmanaged model)
        ClaimsNotes.objects.create(
            claim=claim,
            communication_type=comm_type,
            note_selection=selection,
            note_body=body,
            created_at=timezone.now(),
            created_by=created_by_user
        )
        
        # Success: Redirect back to the dashboard to refresh and show the new note
        return redirect(reverse('claims_dashboard'))

    except Exception as e:
        print(f"Unexpected Error during note creation: {e}")
        return redirect(reverse('claims_dashboard'))
    
@require_http_methods(["POST"])
def create_claim_reminder(request):
    """
    Handles the submission of a new Reminder record.
    Saves the member_no along with the reminder.
    """
    try:
        # Get data from the hidden reminder form fields
        claim_id = request.POST.get('reminder_claim_id')
        reminder_date_str = request.POST.get('reminder_date_hidden')
        emails = request.POST.get('reminder_email_hidden')
        note = request.POST.get('reminder_note_hidden')

        # Basic validation
        if not all([claim_id, reminder_date_str, emails, note]):
            print("ERROR: Missing required fields for reminder submission.")
            return redirect(reverse('claims_dashboard'))

        # Fetch the related Claim object to get member_no
        try:
            claim = Claims.objects.get(pk=claim_id)
        except Claims.DoesNotExist:
            print(f"ERROR: Claim with ID {claim_id} not found for reminder.")
            return redirect(reverse('claims_dashboard'))
            
        # Determine who created the reminder
        created_by_user = request.user.username if request.user.is_authenticated and hasattr(request.user, 'username') else "Consultant (Placeholder)"

        # Create the new Reminders object 
        Reminders.objects.create(
            claim=claim,
            member_no=claim.member_no, # Copy member_no from parent claim
            reminder_date=reminder_date_str, 
            recipient_emails=emails,
            reminder_note=note,
            created_at=timezone.now(),
            created_by=created_by_user
        )
        
        # NOTE: A real implementation would now trigger the email scheduling service.
        
        return redirect(reverse('claims_dashboard'))

    except Exception as e:
        print(f"Unexpected Error during reminder creation: {e}")
        return redirect(reverse('claims_dashboard'))
    
    
from django.views.decorators.http import require_POST


@require_POST
def update_claim_details(request):
    """
    Handles the POST request for updating existing claim details via the modal.
    
    This function extracts the data submitted from the 'Save Changes' button 
    in the claim detail modal and persists the updates to the database.
    """
    if request.method == 'POST':
        claim_id = request.POST.get('claim_id')
        
        # --- Data Extraction ---
        updated_data = {
            'member_no': request.POST.get('member_no'),
            'id_passport': request.POST.get('id_passport'),
            'first_name': request.POST.get('first_name'),
            'surname': request.POST.get('surname'),
            'claim_type': request.POST.get('claim_type'),
            'insurer': request.POST.get('insurer'),
            'consultant': request.POST.get('consultant'),
            'status': request.POST.get('status'),
            'initial_notes': request.POST.get('initial_notes'),
        }

        print(f"Attempting to update Claim ID: {claim_id} with data: {updated_data}")
        
        # ********** IMPLEMENTING CRITICAL DATABASE SECTION **********
        try:
            # 1. Fetch the existing Claim object
            # Note: Ensure Claims model is imported at the top of your actual views.py
            claim = Claims.objects.get(pk=claim_id)

            # 2. Update the fields based on the POST data
            claim.member_no = updated_data['member_no']
            claim.id_passport = updated_data['id_passport']
            claim.first_name = updated_data['first_name']
            claim.surname = updated_data['surname']
            claim.claim_type = updated_data['claim_type']
            claim.insurer = updated_data['insurer']
            claim.consultant = updated_data['consultant']
            claim.status = updated_data['status']
            claim.initial_notes = updated_data['initial_notes']

            # 3. Save the changes to the database
            claim.save()
            
            messages.success(request, f"Claim #{claim_id} details updated successfully.")

        except Claims.DoesNotExist:
            messages.error(request, f"Error: Claim ID {claim_id} not found.")
        except Exception as e:
            messages.error(request, f"Database error during update: {e}")
        # ***************************************************************
            
        # Redirect back to the claims list to refresh the data
        return redirect('claims_dashboard')
        
    return redirect('claims_dashboard')
