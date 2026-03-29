from django.db import models
from datetime import date

class PssubfInbox(models.Model):
    email_id = models.CharField(max_length=255, primary_key=True)
    subject = models.CharField(max_length=255)
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
    task_email_id = models.CharField(max_length=255)
    agent_name = models.CharField(max_length=100)
    note_text = models.TextField()
    classification_at_time = models.CharField(max_length=100)
    status_at_time = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False  # Django will not manage this table
        db_table = 'pssubf_notes'
        
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
    
    # Cessation Date (Note: In MySQL this is generated, so we mark it as read-only)
    cessation_date = models.DateField(editable=False)
    
    # Financials
    stipened_frequency = models.CharField(max_length=50, blank=True, null=True)
    stipened = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
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
        managed = False  # Set to False because we are using MySQL generated columns

    @property
    def is_expired(self):
        """Python-side check to assist with the Bold Red logic in HTML"""
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
        
class ClaimList(models.Model):
    # Foreign Key to Beneficiary
    beneficiary = models.ForeignKey(
        'PssubfBeneficiary', 
        on_delete=models.CASCADE, 
        db_column='beneficiary_membership_number',
        to_field='membership_number',
        related_name='claims'
    )
    
    # Existing & Metadata Fields
    reference_no = models.CharField(max_length=100)
    claim_type = models.CharField(max_length=100) # This maps to Excel "Reason"
    description = models.TextField(blank=True, null=True)
    date_logged = models.DateField(null=True, blank=True) # Maps to "Original Claim Form Date"
    status = models.CharField(max_length=50, default='Pending')
    
    # NEW FIELDS FROM EXCEL DATA
    guardian_name = models.CharField(max_length=255, blank=True, null=True) # Excel: Guardian Name & Surname
    beneficiary_name = models.CharField(max_length=255, blank=True, null=True) # Excel: Beneficiary Name & Surname
    beneficiary_dob = models.DateField(null=True, blank=True) # Excel: Beneficiary Date Of Birth
    termination_date = models.DateField(null=True, blank=True) # Excel: Termination Date
    
    # Financials & Calculations
    portfolio_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00) # Excel: Portfolio Value
    portfolio_date = models.DateField(null=True, blank=True) # Excel: Portfolio Value Date
    amount_requested = models.DecimalField(max_digits=15, decimal_places=2, default=0.00) # Excel: Amount Requested
    monthly_income_payment = models.DecimalField(max_digits=15, decimal_places=2, default=0.00) # Excel: Monthly Income Payment
    age_at_claim = models.CharField(max_length=20, blank=True, null=True) # Excel: Age at Claim Date
    
    # Status & Audit
    supporting_docs_attached = models.CharField(max_length=10, default='No') # Excel: Supporting Documents Attached
    date_paid = models.DateField(null=True, blank=True) # Excel: Date Paid
    loaded_by_agent = models.CharField(max_length=100, blank=True, null=True) # Excel: Loaded by Agent
    
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
    years_to_maturity = models.IntegerField(default=0)
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

    class Meta:
        db_table = 'pssubf_ad_hoc_list'
        managed = False  # Reminder: You must run the ALTER TABLE SQL manually
        
class ClaimAffordability(models.Model):
    claim = models.OneToOneField('ClaimList', on_delete=models.CASCADE, related_name='affordability')
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