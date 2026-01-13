import json
import datetime as dt
from datetime import date, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt 
from django.db import IntegrityError, transaction
from django.contrib import messages
from django.utils import timezone
from .models import ClientClient, ClientReminder
from django.contrib.auth.decorators import login_required

# Import all models
from .models import (
    ClientClient, 
    ClientContact, 
    FicaAddress, 
    FicaResponsiblePerson, 
    FicaDirector, 
    FicaBeneficialOwner,
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
    """Parses DD/MM/YYYY to YYYY-MM-DD format."""
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
        try:
            return datetime.strptime(date_string, '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            return None

def parse_repeating_data(request_data, prefix, field_names):
    """Parses dynamic, repeating form data (directors, contacts, etc)."""
    data = request_data.POST
    files = request_data.FILES if hasattr(request_data, 'FILES') and request_data.FILES else {}
    entities = []
    index = 0
    while True:
        if prefix == 'contact':
            name_key = f'{prefix}-name-{index}'
        else:
            name_key = f'{prefix}_name_{index}'

        if index > 0 and (name_key not in data or not data.get(name_key)):
            break
        if prefix in ('dir', 'owner') and index == 0 and not data.get(f'{prefix}_name_0'):
            break
        if index > 100: 
            break
        
        entity_data = {}
        found_entity = False
        for field in field_names:
            key = f'{prefix}-{field}-{index}' if prefix == 'contact' else f'{prefix}_field_{index}'
            # Fix for specific field naming conventions in your frontend
            if prefix != 'contact': key = f'{prefix}_{field}_{index}'
            
            value = data.get(key)
            if 'postal_check' in field or field.endswith('_q'):
                if 'check' in field: entity_data[field] = (value == 'on')
                elif '_q' in field: entity_data[field] = (value == 'Yes')
            elif field.endswith('_file'):
                file_key = key
                file_obj = files.get(file_key) 
                entity_data[field] = file_obj.name if file_obj else None
                if file_obj: found_entity = True
            else:
                entity_data[field] = value
            if value: found_entity = True
                
        if found_entity:
            entity_data['index'] = index
            entities.append(entity_data)
        index += 1
    return entities

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
    """Detail view fetching ALL related FICA data."""
    # Optimized with prefetch to make the CRM snappier
    client = get_object_or_404(
        ClientClient.objects.prefetch_related(
            'clientcontact_set', 'ficaaddress_set', 'ficadirector_set', 
            'ficabeneficialowner_set', 'ficaresponsibleperson_set'
        ), 
        future_client_number=client_code
    )
    
    client_contacts = client.clientcontact_set.all().order_by('id')
    fica_addresses = client.ficaaddress_set.all().order_by('id')
    fica_resp_person = client.ficaresponsibleperson_set.all().order_by('id')
    fica_directors = client.ficadirector_set.all().order_by('id')
    fica_owners = client.ficabeneficialowner_set.all().order_by('id')
    
    physical_addr = fica_addresses.filter(address_type='physical').first()
    postal_addr = fica_addresses.filter(address_type='postal').first()

    context = {
        'client': client,
        'client_contacts': client_contacts,
        'physical_addr': physical_addr,
        'postal_addr': postal_addr,
        'fica_resp_person': fica_resp_person, 
        'fica_directors': fica_directors,
        'fica_owners': fica_owners,
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
                # 1. Update Core Client Fields
                client.client_name = data.get('client_name')
                client.consultant = data.get('consultant')
                client.industry = data.get('industry')
                client.status = data.get('status')
                client.date_added = safe_parse_date(data.get('date'))
                client.years_active = data.get('years')
                client.employees = data.get('employees') or 0
                client.product = data.get('product')
                client.third_party_contract = (data.get('third_party_contract') == 'yes')
                client.third_party_contact = data.get('third_party_contact')
                client.administrator = data.get('administrator')
                client.umbrella_fund = data.get('umbrella_fund')
                client.insurer = data.get('insurer')
                client.assets = data.get('assets')
                
                # FICA Step 1 & 6 core fields
                client.company_registration_number = data.get('reg_number')
                client.nature_of_relationship = data.get('nat_rel')
                client.purpose_of_relationship = data.get('purp_rel')
                client.source_of_funds = data.get('source_funds')
                client.due_diligence_form_name = data.get('due_diligence_form_name')
                client.declaration_name = data.get('declaration_name')
                client.declaration_delegation = data.get('declaration_delegation')
                client.declaration_date = safe_parse_date(data.get('declaration_date'))

                # Handle File Uploads (Only update if a new file is provided)
                file_map = {
                    'consulting_letter_file': 'consulting_letter_file',
                    'sla_file': 'sla_file',
                    'third_party_doc_file': 'third_party_doc_file',
                    'reg_docs': 'reg_docs_file',
                    'proof_address': 'proof_address_file',
                    'signed_form_upload': 'signed_form_upload'
                }
                for form_key, model_attr in file_map.items():
                    if form_key in files:
                        setattr(client, model_attr, files[form_key])
                
                client.save()

                # 2. Update Addresses (Physical & Postal)
                # Clear and recreate to handle the "Same as physical" checkbox logic
                FicaAddress.objects.filter(client=client).delete()
                
                # Physical
                FicaAddress.objects.create(
                    client=client, address_type='physical',
                    line1=data.get('physical_line1'), line2=data.get('physical_line2'),
                    city=data.get('physical_city'), province=data.get('physical_province'),
                    suburb=data.get('physical_suburb'), postal_code=data.get('physical_code')
                )
                
                # Postal (Only if "same_as_physical" is NOT checked)
                if not data.get('same_as_physical'):
                    FicaAddress.objects.create(
                        client=client, address_type='postal',
                        line1=data.get('postal_line1'), line2=data.get('postal_line2'),
                        city=data.get('postal_city'), province=data.get('postal_province'),
                        suburb=data.get('postal_suburb'), postal_code=data.get('postal_code')
                    )

                # 3. Handle Dynamic Rows (Contacts, Directors, Owners, Responsible Persons)
                # We delete existing relations and re-add them based on the form data
                
                # -- CONTACTS --
                ClientContact.objects.filter(client=client).delete()
                contact_fields = ['name', 'surname', 'job_title', 'email', 'cell', 'landline', 'birthday', 'interests', 'notes']
                for c_data in parse_repeating_data(request, 'contact', contact_fields):
                    ClientContact.objects.create(
                        client=client, name=c_data.get('name'), surname=c_data.get('surname'),
                        job_title=c_data.get('job_title'), email=c_data.get('email'),
                        cell_no=c_data.get('cell'), landline=c_data.get('landline'),
                        birthday=c_data.get('birthday'), interests=c_data.get('interests'),
                        notes=c_data.get('notes')
                    )

                # -- DIRECTORS --
                FicaDirector.objects.filter(client=client).delete()
                dir_fields = [
                    'name', 'surname', 'contact', 'email', 'id', 'designation',
                    'phys_line1', 'phys_line2', 'phys_city', 'phys_province', 'phys_suburb', 'phys_code',
                    'pep_q', 'pep_reason', 'pip_q', 'pip_reason', 'ppo_q', 'ppo_reason', 'kca_q', 'kca_reason'
                ]
                for d_data in parse_repeating_data(request, 'dir', dir_fields):
                    FicaDirector.objects.create(
                        client=client, name=d_data.get('name'), surname=d_data.get('surname'),
                        contact_number=d_data.get('contact'), email_address=d_data.get('email'),
                        id_number=d_data.get('id'), designation=d_data.get('designation'),
                        is_pep=(d_data.get('pep_q') == 'Yes'), pep_reason=d_data.get('pep_reason'),
                        is_pip=(d_data.get('pip_q') == 'Yes'), pip_reason=d_data.get('pip_reason')
                        # ... continue mapping other fields ...
                    )

                # -- RESPONSIBLE PERSONS --
                FicaResponsiblePerson.objects.filter(client=client).delete()
                resp_fields = ['name', 'surname', 'designation', 'id_num', 'contact', 'email', 'line1', 'line2', 'city', 'province', 'suburb', 'code']
                for r_data in parse_repeating_data(request, 'resp', resp_fields):
                    FicaResponsiblePerson.objects.create(
                        client=client, name=r_data.get('name'), surname=r_data.get('surname'),
                        designation=r_data.get('designation'), id_number=r_data.get('id_num'),
                        email_address=r_data.get('email'), contact_number=r_data.get('contact')
                    )

            messages.success(request, f"Client {client_code} updated successfully!")
            return redirect('client_info', client_code=client_code)
            
        except Exception as e:
            messages.error(request, f"Critical Error during save: {str(e)}")
            print(f"Error: {e}")

    # GET Request: Prepare context
    contacts = client.clientcontact_set.all()
    addresses = client.ficaaddress_set.all()
    
    context = {
        'client': client,
        'client_contacts': contacts,
        'physical_addr': addresses.filter(address_type='physical').first(),
        'postal_addr': addresses.filter(address_type='postal').first(),
        'fica_resp_person': client.ficaresponsibleperson_set.all(),
        'fica_directors': client.ficadirector_set.all(),
        'fica_owners': client.ficabeneficialowner_set.all(),
        'date_added_formatted': client.date_added.strftime('%d/%m/%Y') if client.date_added else '',
        'declaration_date_formatted': client.declaration_date.strftime('%d/%m/%Y') if client.declaration_date else '',
    }
    return render(request, 'consulting/edit_client.html', context)

@require_http_methods(["GET", "POST"])
def add_client_view(request):
    if request.method == 'POST':
        data = request.POST
        client_code = data.get('client_number', get_next_client_number())
        try:
            with transaction.atomic():
                client = ClientClient.objects.create(
                    future_client_number=client_code, 
                    client_name=data.get('client_name', 'N/A'),
                    consultant=data.get('consultant', 'N/A'),
                    date_added=safe_parse_date(data.get('date')),
                    status=data.get('status', 'New')
                )
                FicaAddress.objects.create(client=client, address_type='physical', line1=data.get('physical_line1'))
            messages.success(request, f"New Client {client_code} added!")
            return redirect('client_info', client_code=client_code) 
        except Exception as e:
            messages.error(request, f"Error adding client: {e}")
            
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
    if request.method == 'POST':
        try:
            Lead.objects.create(
                company_name=request.POST['company_name'],
                contact_person=request.POST['contact_person'],
                date_received=dt.datetime.strptime(request.POST['date_received'], '%Y-%m-%d').date(),
                status='New',
                assigned_to=request.POST.get('assigned_to', 'Unassigned')
            )
            return redirect('lead_list')
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, 'consulting/add_new_lead.html', {'current_date': dt.date.today().strftime('%Y-%m-%d')})

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

def claims_dashboard(request):
    claims_queryset = Claims.objects.all().order_by('-created_date')
    all_notes = ClaimsNotes.objects.all().order_by('-created_at')
    
    notes_by_claim = {}
    for note in all_notes:
        note_data = {'body': note.note_body, 'user': note.created_by, 'date': note.created_at.strftime("%Y-%m-%d")}
        notes_by_claim.setdefault(note.claim_id, []).append(note_data)
        
    claims_list = []
    for c in claims_queryset:
        claims_list.append({
            'id': c.id, 'memberNo': c.member_no, 'firstName': c.first_name, 'surname': c.surname,
            'status': c.status, 'notes': notes_by_claim.get(c.id, [])
        })
        
    context = {
        'claims': claims_queryset,
        'claims_json': json.dumps(claims_list),
        'consultants': CONSULTANTS, 'insurers': INSURERS, 'claim_types': CLAIM_TYPES
    }
    return render(request, 'consulting/claims_dashboard.html', context)

@require_POST
def update_claim_details(request):
    claim_id = request.POST.get('claim_id')
    claim = get_object_or_404(Claims, pk=claim_id)
    try:
        claim.status = request.POST.get('status')
        claim.save()
        messages.success(request, "Claim updated.")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect('claims_dashboard')

@require_POST
def create_claim_note(request):
    claim = get_object_or_404(Claims, pk=request.POST.get('note_claim_id'))
    ClaimsNotes.objects.create(
        claim=claim, note_body=request.POST.get('note_body'),
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
        Claims.objects.create(
            member_no=request.POST.get('new_member_no'),
            first_name=request.POST.get('new_first_name'),
            surname=request.POST.get('new_surname'),
            created_date=date.today()
        )
    except Exception as e:
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

# ==========================================
# 2. CALENDAR & FILTERING
# ==========================================
@login_required
def client_calendar(request):
    # Fetch all clients for the dropdowns
    clients = ClientClient.objects.all().order_by('client_name')
    
    # Get client_id from the URL (the GET request from the filter bar)
    filter_client_id = request.GET.get('view_client')
    selected_client = None

    # THE FIX: This logic must exist and be the ONLY 'client_calendar' function
    if filter_client_id and filter_client_id.strip():
        try:
            # Show future reminders strictly for the SPECIFIC selected client
            reminders_list = ClientReminder.objects.filter(
                client_id=filter_client_id,
                reminder_date__gte=date.today(),
                is_dismissed=False
            ).order_by('reminder_date')
            
            # This allows the template to show "Upcoming Schedule for: [Name]"
            selected_client = ClientClient.objects.get(id=filter_client_id)
        except (ClientClient.DoesNotExist, ValueError):
            reminders_list = ClientReminder.objects.none()
    else:
        # Default: Show ALL upcoming reminders for all clients
        reminders_list = ClientReminder.objects.filter(
            reminder_date__gte=date.today(),
            is_dismissed=False
        ).order_by('reminder_date')

    return render(request, 'calendar.html', {
        'clients': clients,
        'reminders_list': reminders_list,
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
        title = request.POST.get('title')
        note = request.POST.get('note')

        if client_id and reminder_date:
            ClientReminder.objects.create(
                client_id=client_id,
                title=title,
                note=note,
                reminder_date=reminder_date,
                created_by=request.user, 
                is_dismissed=False
            )
        
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