from django.db import models

# ====================================================================
# 1. CORE CLIENT AND FICA DETAILS (client_client)
# ====================================================================

class ClientClient(models.Model):
    # Tab 1: General Information
    future_client_number = models.CharField(max_length=10, unique=True)
    # NOTE: Re-added client_name field, as it is mandatory for the form submission logic in views.py
    client_name = models.CharField(max_length=255, null=True, blank=True)
    consultant = models.CharField(max_length=50)
    industry = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=50)
    date_added = models.DateField(null=True, blank=True)
    years_active = models.IntegerField(null=True, blank=True)
    employees = models.IntegerField(null=True, blank=True)

    # Tab 1: Product & Agreement Details
    product = models.CharField(max_length=50, null=True, blank=True)
    third_party_contract = models.BooleanField(default=False)
    third_party_contact = models.CharField(max_length=50, null=True, blank=True)
    administrator = models.CharField(max_length=50, null=True, blank=True)
    umbrella_fund = models.CharField(max_length=50, null=True, blank=True)
    insurer = models.CharField(max_length=50, null=True, blank=True)
    assets = models.TextField(null=True, blank=True)
    
    # Tab 1: Document Status (paths/names)
    consulting_letter_status = models.BooleanField(default=False)
    consulting_letter_file = models.CharField(max_length=255, null=True, blank=True)
    sla_status = models.BooleanField(default=False)
    sla_file = models.CharField(max_length=255, null=True, blank=True)
    third_party_doc_status = models.BooleanField(default=False)
    third_party_doc_file = models.CharField(max_length=255, null=True, blank=True)

    # FICA Status (for dashboard/reporting)
    fica_dd_completed = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    bulk_email_status = models.BooleanField(default=False)

    # FICA Step 7: Transaction Information (Embedded in ClientClient for simplicity)
    nature_of_relationship = models.CharField(max_length=100, default='Employer / Pension Fund')
    purpose_of_relationship = models.CharField(max_length=100, default='Employee Pension Fund')
    source_of_funds = models.CharField(max_length=100, default='Payroll')

    # FICA Declaration (Step 7)
    due_diligence_form_name = models.CharField(max_length=255, null=True, blank=True)
    declaration_name = models.CharField(max_length=100, null=True, blank=True)
    declaration_delegation = models.CharField(max_length=100, null=True, blank=True)
    declaration_date = models.DateField(null=True, blank=True)
    signed_form_upload = models.CharField(max_length=255, null=True, blank=True) # Storing file path

    class Meta:
        managed = False  # Tells Django not to manage this table's creation/modification
        db_table = 'client_client'
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
    
    def __str__(self):
        return self.client_name or self.future_client_number

# ====================================================================
# 2. CONTACTS (client_contact)
# ====================================================================

class ClientContact(models.Model):
    client = models.ForeignKey(ClientClient, on_delete=models.DO_NOTHING, db_column='client_id')
    
    name = models.CharField(max_length=100, null=True, blank=True)
    surname = models.CharField(max_length=100, null=True, blank=True)
    job_title = models.CharField(max_length=100, null=True, blank=True)
    landline = models.CharField(max_length=50, null=True, blank=True)
    cell_no = models.CharField(max_length=50, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    physical_address = models.TextField(null=True, blank=True)
    postal_address = models.TextField(null=True, blank=True)
    city_town = models.CharField(max_length=50, null=True, blank=True)
    province = models.CharField(max_length=50, null=True, blank=True)
    birthday = models.CharField(max_length=50, null=True, blank=True) # Storing as char for DD/MM/YYYY format
    notes = models.TextField(null=True, blank=True)
    interests = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'client_contact'
        verbose_name = 'Client Contact'
        verbose_name_plural = 'Client Contacts'

# ====================================================================
# 3. FICA ADDRESS (fica_address - For main company addresses)
# ====================================================================

class FicaAddress(models.Model):
    client = models.ForeignKey(ClientClient, on_delete=models.DO_NOTHING, db_column='client_id')
    
    address_type = models.CharField(max_length=20) # 'physical', 'postal'
    line1 = models.CharField(max_length=150)
    line2 = models.CharField(max_length=150, null=True, blank=True)
    province = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    suburb = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    
    class Meta:
        managed = False
        db_table = 'fica_address'
        verbose_name = 'FICA Address'
        verbose_name_plural = 'FICA Addresses'

# ====================================================================
# 4. RESPONSIBLE PERSON (fica_responsibleperson - Step 4)
# ====================================================================

class FicaResponsiblePerson(models.Model):
    client = models.ForeignKey(ClientClient, on_delete=models.DO_NOTHING, db_column='client_id')
    
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)
    id_number = models.CharField(max_length=50)
    contact_number = models.CharField(max_length=50, null=True, blank=True)
    email_address = models.CharField(max_length=100, null=True, blank=True)

    # Physical Home Address Fields
    resp_line1 = models.CharField(max_length=150, null=True, blank=True)
    resp_line2 = models.CharField(max_length=150, null=True, blank=True)
    resp_province = models.CharField(max_length=50, null=True, blank=True)
    resp_city = models.CharField(max_length=100, null=True, blank=True)
    resp_suburb = models.CharField(max_length=100, null=True, blank=True)
    resp_code = models.CharField(max_length=20, null=True, blank=True)
    
    # Document Uploads (File paths/names)
    circular_upload_file = models.CharField(max_length=255, null=True, blank=True)
    doc_signed_upload_file = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        managed = False
        db_table = 'fica_responsibleperson'
        verbose_name = 'FICA Responsible Person'
        verbose_name_plural = 'FICA Responsible Persons'

# ====================================================================
# 5. DIRECTOR (fica_director - Step 5)
# ====================================================================

class FicaDirector(models.Model):
    client = models.ForeignKey(ClientClient, on_delete=models.DO_NOTHING, db_column='client_id')
    
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)
    id_number = models.CharField(max_length=50)
    contact_number = models.CharField(max_length=50, null=True, blank=True)
    email_address = models.CharField(max_length=100, null=True, blank=True)
    
    # Addresses
    phys_line1 = models.CharField(max_length=150)
    phys_line2 = models.CharField(max_length=150, null=True, blank=True)
    phys_province = models.CharField(max_length=50, null=True, blank=True)
    phys_city = models.CharField(max_length=100, null=True, blank=True)
    phys_suburb = models.CharField(max_length=100, null=True, blank=True)
    phys_code = models.CharField(max_length=20, null=True, blank=True)
    postal_same_as_phys = models.BooleanField(default=True)
    postal_line1 = models.CharField(max_length=150, null=True, blank=True)
    postal_line2 = models.CharField(max_length=150, null=True, blank=True)
    postal_province = models.CharField(max_length=50, null=True, blank=True)

    # Document Uploads
    proof_addr_file = models.CharField(max_length=255, null=True, blank=True)
    id_copy_file = models.CharField(max_length=255, null=True, blank=True)
    
    # PEP/PIP/KCA Details
    is_pep = models.BooleanField(default=False)
    pep_reason = models.TextField(null=True, blank=True)
    is_pip = models.BooleanField(default=False)
    pip_reason = models.TextField(null=True, blank=True)
    is_ppo = models.BooleanField(default=False)
    ppo_reason = models.TextField(null=True, blank=True)
    is_kca = models.BooleanField(default=False)
    kca_reason = models.TextField(null=True, blank=True)
    
    class Meta:
        managed = False
        db_table = 'fica_director'
        verbose_name = 'FICA Director'
        verbose_name_plural = 'FICA Directors'

# ====================================================================
# 6. BENEFICIAL OWNER (fica_beneficialowner - Step 6)
# ====================================================================

class FicaBeneficialOwner(models.Model):
    client = models.ForeignKey(ClientClient, on_delete=models.DO_NOTHING, db_column='client_id')
    
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)
    id_number = models.CharField(max_length=50)
    contact_number = models.CharField(max_length=50, null=True, blank=True)
    email_address = models.CharField(max_length=100, null=True, blank=True)
    
    # Addresses
    phys_line1 = models.CharField(max_length=150)
    phys_line2 = models.CharField(max_length=150, null=True, blank=True)
    phys_province = models.CharField(max_length=50, null=True, blank=True)
    phys_city = models.CharField(max_length=100, null=True, blank=True)
    phys_suburb = models.CharField(max_length=100, null=True, blank=True)
    phys_code = models.CharField(max_length=20, null=True, blank=True)
    postal_same_as_phys = models.BooleanField(default=True)
    postal_line1 = models.CharField(max_length=150, null=True, blank=True)
    postal_line2 = models.CharField(max_length=150, null=True, blank=True)
    postal_province = models.CharField(max_length=50, null=True, blank=True)

    # Document Uploads
    proof_addr_file = models.CharField(max_length=255, null=True, blank=True)
    id_copy_file = models.CharField(max_length=255, null=True, blank=True)
    
    # PEP/PIP/KCA Details
    is_pep = models.BooleanField(default=False)
    pep_reason = models.TextField(null=True, blank=True)
    is_pip = models.BooleanField(default=False)
    pip_reason = models.TextField(null=True, blank=True)
    is_ppo = models.BooleanField(default=False)
    ppo_reason = models.TextField(null=True, blank=True)
    is_kca = models.BooleanField(default=False)
    kca_reason = models.TextField(null=True, blank=True)
    
    class Meta:
        managed = False
        db_table = 'fica_beneficialowner'
        verbose_name = 'FICA Beneficial Owner'
        verbose_name_plural = 'FICA Beneficial Owners'
    
class Lead(models.Model):
    id = models.IntegerField(primary_key=True) 
    lead_received_from = models.CharField(max_length=100, null=True, blank=True)
    date_received = models.DateField(null=True, blank=True)
    company_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, null=True, blank=True)
    contact_number = models.CharField(max_length=50, null=True, blank=True) 
    contact_email = models.EmailField(max_length=254, null=True, blank=True) 
    product_required = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, default='New')
    assigned_to = models.CharField(max_length=100, null=True, blank=True)
    date_accepted = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    last_follow_up = models.DateField(null=True, blank=True)
    
    # NEW FIELDS TO STORE LAST COMMUNICATION DETAILS
    communication_type = models.CharField(max_length=50, null=True, blank=True)
    note_type = models.CharField(max_length=50, null=True, blank=True)
    
    internal_notes = models.TextField(null=True, blank=True) # Stores history log

    class Meta:
        managed = False
        db_table = 'consulting_lead' 
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'

    def __str__(self):
        return f"{self.company_name} - {self.status}"
    
class Claims(models.Model):
    # Primary Key
    id = models.AutoField(primary_key=True)
    
    # Member Information
    member_no = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    id_passport = models.CharField(max_length=50)
    
    # Employment Details
    employer_code = models.CharField(max_length=50)
    employer_name = models.CharField(max_length=255)
    
    # Insurance Detail (NEW FIELD)
    insurer = models.CharField(max_length=100)
    
    # Claim Details
    claim_type = models.CharField(max_length=100)  # e.g., 'Funeral - main member', 'Divorce', 'Retirement'
    consultant = models.CharField(max_length=100)
    last_action = models.CharField(max_length=255, default="Initial Submission")
    status = models.CharField(max_length=20, default="Pending") # e.g., 'Pending', 'InProgress', 'Resolved'
    created_date = models.DateField(auto_now_add=True)
    initial_notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'claims_claims'
        verbose_name_plural = 'Claims'
        
    def __str__(self):
        return f"Claim #{self.id} - {self.surname}, {self.claim_type}"
    
class ClaimsNotes(models.Model):
    # Foreign Key linking the note back to the specific claim
    # Since this model is unmanaged, we use DO_NOTHING for the on_delete rule.
    claim = models.ForeignKey(Claims, on_delete=models.DO_NOTHING, related_name='notes') 
    
    # Fields matching your database table
    communication_type = models.CharField(max_length=50) 
    note_selection = models.CharField(max_length=100)    
    note_body = models.TextField()
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100) 
    
    class Meta:
        managed = False
        db_table = 'claimsnotes'  # <-- THIS IS THE CRUCIAL FIX
        
    def __str__(self):
        return f"Note {self.id} for Claim {self.claim.id}"
    
class Reminders(models.Model):
    """
    Unmanaged model corresponding to the 'reminders' database table.
    Stores scheduled reminder data. Must be created manually via SQL.
    """
    claim = models.ForeignKey(Claims, on_delete=models.DO_NOTHING, related_name='reminders')
    member_no = models.CharField(
        max_length=50, 
        help_text="Member Number copied from the parent claim."
    ) 
    reminder_date = models.DateField()
    recipient_emails = models.TextField(
        help_text="Comma separated list of emails."
    )
    reminder_note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    
    class Meta:
        managed = False
        db_table = 'reminders' # Must match the actual database table name
        indexes = [
            models.Index(fields=['claim', 'member_no']),
        ]
        
    def __str__(self):
        return f"Reminder for Claim {self.claim.id} (Member {self.member_no}) on {self.reminder_date}"
    
class ClientReminder(models.Model):
    """
    Unmanaged model for client-specific calendar reminders.
    Table created manually via SQL referencing 'client_client'.
    """
    client = models.ForeignKey(ClientClient, on_delete=models.CASCADE, db_column='client_id')
    title = models.CharField(max_length=200)
    note = models.TextField()
    reminder_date = models.DateField()
    # Using Django's built-in User table for auth_user reference
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, db_column='created_by_id')
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'client_reminders'
        verbose_name = 'Client Reminder'
        verbose_name_plural = 'Client Reminders'

    def __str__(self):
        return f"{self.title} - {self.client.client_name}"