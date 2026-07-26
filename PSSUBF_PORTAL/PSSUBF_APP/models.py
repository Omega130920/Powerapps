from django.db import models
from datetime import date

class PssubfInbox(models.Model):
    email_id = models.CharField(max_length=255, primary_key=True)
    # Added null=True and blank=True to handle emails with no subject line
    subject = models.CharField(max_length=255, null=True, blank=True) 
    sender = models.CharField(max_length=255)
    received_timestamp = models.DateTimeField()
    snippet = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default='Pending')

    class Meta:
        managed = False
        db_table = 'pssubf_inbox'

class PssubfDelegate(models.Model):
    email_id = models.CharField(max_length=255, primary_key=True)
    assigned_agent = models.CharField(max_length=150, blank=True, null=True)
    member_group_code = models.CharField(max_length=100, blank=True, null=True)
    email_category = models.CharField(max_length=100, blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    sender = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, default='Assigned')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def received_timestamp(self):
        """Fetches the original received time from the Inbox table"""
        # We import inside the method to avoid circular import errors
        from .models import PssubfInbox 
        inbox_item = PssubfInbox.objects.filter(email_id=self.email_id).first()
        return inbox_item.received_timestamp if inbox_item else None

    class Meta:
        managed = False
        db_table = 'pssubf_delegate'

class PssubfAction(models.Model):
    id = models.AutoField(primary_key=True)
    task_email_id = models.CharField(max_length=255)
    action_type = models.CharField(max_length=100)
    action_user = models.CharField(max_length=100)
    note_content = models.TextField()
    action_timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'pssubf_actions'
        
class PssubfOutlookToken(models.Model):
    # Isolated from the User model to prevent cross-database errors
    service_account = models.CharField(max_length=100, unique=True)
    access_token = models.TextField()
    expires_at = models.DateTimeField()

    class Meta:
        managed = False  # Managed manually in MySQL
        db_table = 'pssubf_outlook_token'
        
class PssubfNote(models.Model):
    # primary_key=True is required if 'id' is your PK in MySQL
    id = models.AutoField(primary_key=True) 
    
    # task_email_id: used to link notes to specific emails or "PROFILE_XXX"
    task_email_id = models.CharField(max_length=255, db_column='task_email_id', blank=True, null=True)
    
    # agent_name: Stores the username of the person who wrote the note
    agent_name = models.CharField(max_length=100, db_column='agent_name', blank=True, null=True)
    
    # note_text: The actual content of the note
    note_text = models.TextField(db_column='note_text', blank=True, null=True)
    
    # classification_at_time: e.g., "General Note", "Claim Note", etc.
    classification_at_time = models.CharField(max_length=100, db_column='classification_at_time', blank=True, null=True)
    
    # status_at_time: Captures the member/task status when the note was made
    status_at_time = models.CharField(max_length=50, db_column='status_at_time', blank=True, null=True)
    
    # created_at: Maps to the timestamp column in MySQL
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')

    class Meta:
        managed = False  # Django will not attempt to create or alter this table
        db_table = 'pssubf_notes'
        verbose_name = "Pssubf Note"
        verbose_name_plural = "Pssubf Notes"

    def __str__(self):
        return f"Note by {self.agent_name} on {self.created_at}"
        
class PssubfBeneficiary(models.Model):
    # Member Identification
    membership_number = models.CharField(max_length=100, primary_key=True)
    old_membership_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Member Personal Details
    title = models.CharField(max_length=20, blank=True, null=True)
    initials = models.CharField(max_length=10, blank=True, null=True)
    first_name = models.CharField(max_length=255)
    second_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255)
    id_number = models.CharField(max_length=50, unique=True)
    dob = models.DateField()
    gender = models.CharField(max_length=20, blank=True, null=True)
    employee_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Fund Dates
    fund_join_date = models.DateField(blank=True, null=True)
    
    # Cessation Date (MySQL Generated Column)
    cessation_date = models.DateField(editable=False)
    
    # Financials
    stipened_frequency = models.CharField(max_length=50, blank=True, null=True)
    stipened = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_fund_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    # NEW: Added to store the Date of Value for the fund
    portfolio_date = models.DateField(blank=True, null=True)
    
    # Contact Info
    mobile_1 = models.CharField(max_length=20, blank=True, null=True)
    email_1 = models.EmailField(max_length=255, blank=True, null=True)
    mobile_2 = models.CharField(max_length=20, blank=True, null=True)
    email_2 = models.EmailField(max_length=255, blank=True, null=True)
    mobile_3 = models.CharField(max_length=20, blank=True, null=True)
    email_3 = models.EmailField(max_length=255, blank=True, null=True)
    
    # Guardian Details
    guardian_mobile = models.CharField(max_length=20, blank=True, null=True)
    guardian_email = models.EmailField(max_length=255, blank=True, null=True)
    guardian_title = models.CharField(max_length=20, blank=True, null=True)
    guardian_first_name = models.CharField(max_length=255, blank=True, null=True)
    guardian_second_name = models.CharField(max_length=255, blank=True, null=True)
    guardian_last_name = models.CharField(max_length=255, blank=True, null=True)
    guardian_initial = models.CharField(max_length=10, blank=True, null=True)
    guardian_dob = models.DateField(blank=True, null=True)
    guardian_id_number = models.CharField(max_length=50, blank=True, null=True)
    guardian_id_type = models.CharField(max_length=50, blank=True, null=True)
    guardian_gender = models.CharField(max_length=20, blank=True, null=True)
    guardian_address = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pssubf_beneficiaries'
        managed = False  # Controlled by MySQL

    @property
    def is_expired(self):
        return date.today() >= self.cessation_date

    def __str__(self):
        return f"{self.membership_number} - {self.first_name} {self.last_name}"
    
class PssubfProfileNote(models.Model):
    membership_number = models.CharField(max_length=100)
    agent_name = models.CharField(max_length=100)
    note_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'pssubf_profile_notes'

class PssubfDirectEmail(models.Model):
    membership_number = models.CharField(max_length=100)
    agent_name = models.CharField(max_length=100)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body_html = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'pssubf_direct_emails'
        
from django.db import models

from django.db import models

class ClaimList(models.Model):
    # This is the ONLY field. It handles the DB column AND the relationship.
    beneficiary = models.ForeignKey(
        'PssubfBeneficiary', 
        on_delete=models.CASCADE, 
        db_column='beneficiary_membership_number', # The actual column name in MySQL
        to_field='membership_number',               # The column it links to in the other table
        related_name='claims',
        null=True,
        blank=True
    )
    
    reference_no = models.CharField(max_length=100)
    claim_type = models.CharField(max_length=100) 
    description = models.TextField(blank=True, null=True)
    date_logged = models.DateField(null=True, blank=True) 
    status = models.CharField(max_length=50, default='Pending')
    
    guardian_name = models.CharField(max_length=255, blank=True, null=True) 
    beneficiary_name = models.CharField(max_length=255, blank=True, null=True) 
    beneficiary_dob = models.DateField(null=True, blank=True) 
    termination_date = models.DateField(null=True, blank=True) 
    
    portfolio_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00) 
    portfolio_date = models.DateField(null=True, blank=True) 
    amount_requested = models.DecimalField(max_digits=15, decimal_places=2, default=0.00) 
    monthly_income_payment = models.DecimalField(max_digits=15, decimal_places=2, default=0.00) 
    age_at_claim = models.CharField(max_length=20, blank=True, null=True) 
    
    supporting_docs_attached = models.CharField(max_length=10, default='No') 
    date_paid = models.DateField(null=True, blank=True) 
    loaded_by_agent = models.CharField(max_length=100, blank=True, null=True) 
    
    attachment_path = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pssubf_claim_list'
        managed = False

from django.db import models

class AdHocList(models.Model):
    # Foreign Key Relation to Beneficiary
    beneficiary = models.ForeignKey(
        'PssubfBeneficiary', 
        on_delete=models.CASCADE, 
        db_column='beneficiary_membership_number',
        to_field='membership_number',
        related_name='adhoc_records'
    )
    
    # Header & Identity
    title = models.CharField(max_length=255)  # Stores the 'Reason' selected from dropdown
    status = models.CharField(max_length=50, default='Created')
    
    # Financial Fields
    portfolio_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    portfolio_date = models.DateField(null=True, blank=True)
    amount_requested = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Calculation Results
    # UPDATED: Changed to DecimalField to prevent rounding (e.g., 6.2 instead of 6)
    years_to_maturity = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Changed to CharField to store the formatted "%" string from the UI logic
    affordability_calculation = models.CharField(max_length=20, blank=True, null=True)
    
    # Dates & Processing
    claim_form_date = models.DateField(null=True, blank=True)
    date_paid = models.DateField(null=True, blank=True)  # New Field Added
    date_created = models.DateField(auto_now_add=True)
    
    # Attachments & Notes
    supporting_docs_attached = models.CharField(max_length=10, default='No')
    attachment_path = models.CharField(max_length=255, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)  # Stores 'Claim Note' and Agent Tracking

    @property
    def age_at_claim_calc(self):
        """Calculates exact decimal age at the time of claim (e.g., 11.8)"""
        if self.beneficiary and self.beneficiary.dob and self.claim_form_date:
            days_diff = (self.claim_form_date - self.beneficiary.dob).days
            return round(days_diff / 365.25, 1)
        return 0.0

    class Meta:
        db_table = 'pssubf_ad_hoc_list'
        managed = False  # Reminder: You must run the ALTER TABLE SQL manually
        
class ClaimAffordability(models.Model):
    # FIXED: Added null/blank to resolve IntegrityError during manual audits
    # Added db_column to ensure exact match with MySQL
    claim = models.OneToOneField(
        'ClaimList', 
        on_delete=models.CASCADE, 
        related_name='affordability',
        null=True, 
        blank=True,
        db_column='claim_id'
    )
    membership_number = models.CharField(max_length=100)
    majority_date = models.DateField()
    years_to_majority = models.DecimalField(max_digits=5, decimal_places=2)
    months_to_majority = models.IntegerField()
    total_stipend_commitment = models.DecimalField(max_digits=15, decimal_places=2)
    fund_after_stipend = models.DecimalField(max_digits=15, decimal_places=2)
    final_projected_balance = models.DecimalField(max_digits=15, decimal_places=2)
    requires_letter = models.BooleanField(default=False)
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pssubf_claim_affordability'
        managed = False  # Set to False as you are managing this via SQL statements

class SystemLog(models.Model):
    # Dropdown choices
    CATEGORY_CHOICES = [
        ('Query', 'Query'),
        ('Claim', 'Claim'),
        ('Follow-up', 'Follow-up'),
        ('Urgent', 'Urgent'),
        ('Unsure', 'Unsure'),
    ]

    STATUS_CHOICES = [
        ('In Progress', 'In Progress'),
        ('Delegated', 'Delegated'),
    ]

    # Added MIP Number
    mip_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Text inputs
    log_title = models.CharField(max_length=200)
    
    # New Call/Task Metadata
    call_direction = models.CharField(max_length=50, blank=True, null=True)
    call_method = models.CharField(max_length=50, blank=True, null=True)
    call_type = models.CharField(max_length=150, blank=True, null=True)
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Query')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='In Progress')
    
    # Note textarea
    note_content = models.TextField()
    
    # Metadata
    created_by = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'pssubf_system_log'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.mip_number} | {self.log_title}"

class ClaimHistory(models.Model):
    claim_reference = models.CharField(max_length=100)
    action_type = models.CharField(max_length=100)
    note_content = models.TextField(blank=True, null=True)
    attachment_path = models.CharField(max_length=255, blank=True, null=True)
    agent_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pssubf_claim_history'
        managed = False