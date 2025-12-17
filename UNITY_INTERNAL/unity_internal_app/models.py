from decimal import Decimal
# NOTE: Removed 'from time import timezone' as it conflicts with 'from django.utils import timezone'
from django.db import models
from django.utils import timezone 
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User # Explicitly import User for claim notes FK

User = get_user_model() # Define the User model alias (moved to the top)

# --- Data Source Model 2: Unity Mg Listing (Primary Details) ---
class UnityMgListing(models.Model):
    a_company_code = models.CharField(max_length=255, primary_key=True, db_column='A_Company_Code')
    b_company_name = models.CharField(max_length=255, null=True, blank=True, db_column='B_Company_Name')
    c_agent = models.CharField(max_length=255, null=True, blank=True, db_column='C_Agent')
    d_company_status = models.CharField(max_length=255, null=True, blank=True, db_column='D_Company_Status')
    e_payment_method = models.CharField(max_length=255, null=True, blank=True, db_column='E_Payment_Method')
    f_billing_method = models.CharField(max_length=255, null=True, blank=True, db_column='F_Billing_Method')
    g_current_fiscal = models.CharField(max_length=255, null=True, blank=True, db_column='G_Current_Fiscal')
    h_current_status = models.CharField(max_length=255, null=True, blank=True, db_column='H_Current_Status')
    i_last_recon = models.CharField(max_length=255, null=True, blank=True, db_column='I_Last_Recon')
    j_arrears = models.CharField(max_length=255, null=True, blank=True, db_column='J_Arrears')
    contact_email = models.CharField(max_length=255, null=True, blank=True, db_column='CONTACT_EMAIL')

    # --- NEW ADDED FIELDS (Consolidated) ---
    recon_contact_1_name = models.CharField(max_length=255, null=True, blank=True, db_column='recon_contact_1_name')
    recon_contact_1_email = models.CharField(max_length=255, null=True, blank=True, db_column='recon_contact_1_email')
    recon_contact_2_name = models.CharField(max_length=255, null=True, blank=True, db_column='recon_contact_2_name')
    recon_contact_2_email = models.CharField(max_length=255, null=True, blank=True, db_column='recon_contact_2_email')
    
    commencement_date = models.DateField(null=True, blank=True, db_column='Commencement_Date')
    fund_status = models.CharField(max_length=255, null=True, blank=True, db_column='Fund_status')
    fund_status_date = models.DateField(null=True, blank=True, db_column='fund_status_date')

    class Meta:
        managed = False
        db_table = 'internal_mg_list'
        verbose_name_plural = 'internal_mg_list'

    def __str__(self):
        return self.b_company_name
    
# --- Utility Model: Used for Client Notes ---
class ClientNotes(models.Model):
    """
    Model to store client notes related to a UnityMgListing.
    """
    a_company_code = models.CharField(db_column='Member_Group_Code', max_length=255) 
    notes = models.TextField(db_column='notes')
    user = models.CharField(db_column='User_Name', max_length=255) 
    date = models.DateTimeField(db_column='date', auto_now_add=True) 

    def __str__(self):
        return f"Note on {self.a_company_code} by {self.user}"

    class Meta:
        verbose_name_plural = 'Client Notes'
        db_table = 'internal_mg_notes'
        managed = False
        
# --- Data Source Model 1: Internal Funds (Fallback Data) ---
class InternalFunds(models.Model):
    A_Company_Code = models.CharField(
        max_length=225, 
        db_column='A_Company_Code', 
        primary_key=True
    )
    B_Company_Name = models.CharField(
        max_length=225, 
        db_column='B_Company_Name'
    )
    Source = models.CharField(
        max_length=10, 
        db_column='Source'
    )
    D_Company_Status = models.CharField(
        max_length=225, 
        db_column='D_Company_Status'
    )

    class Meta:
        managed = False 
        db_table = 'internal_funds' 

    def __str__(self):
        return f"{self.A_Company_Code} - {self.B_Company_Name} - {self.Source} - {self.D_Company_Status}"
    
# --- Data Source Model 4: Import Bank (Imported Transactions) ---
class ImportBank(models.Model):
    """
    Unmanaged model for temporary Excel data import into the MySQL 'importbank' table.
    """
    # Assuming 'id' is implicit or manually set as PK in DB.
    bank_account_name = models.CharField(max_length=255, db_column='Bank_account_name')
    account_number = models.CharField(max_length=255, db_column='Account_number')
    statement_reference = models.CharField(max_length=255, db_column='Statement_reference', null=True, blank=True)
    date = models.DateField(db_column='DATE') 
    balance = models.DecimalField(max_digits=15, decimal_places=2, db_column='Balance', null=True, blank=True)
    transaction_amount = models.DecimalField(max_digits=15, decimal_places=2, db_column='Transaction_amount')
    transaction_description = models.TextField(db_column='Transaction_description', null=True, blank=True)
    
    internal_identification = models.CharField(max_length=255, db_column='INTERNAL_IDENTIFICATION', null=True, blank=True)
    specialist = models.CharField(max_length=255, db_column='Specialist', null=True, blank=True)
    date_identified = models.DateField(null=True, blank=True, db_column='Date_identified')
    fiscal = models.CharField(max_length=255, db_column='Fiscal', null=True, blank=True)
    comments = models.TextField(db_column='Comments', null=True, blank=True)
    interim_fiscal = models.CharField(max_length=255, db_column='Interim_fiscal', null=True, blank=True)
    allocated_company_code = models.CharField(
        max_length=255, 
        db_column='Reconned', 
        null=True, 
        blank=True
    )

    class Meta:
        managed = False 
        db_table = 'importbank' 

    def __str__(self):
        return f"Import Record: {self.account_number} on {self.date}"

# --- Data Source Model 3: Unity Bill Records (CRITICAL FIX: New PK 'id') ---
class UnityBill(models.Model):
    """
    Unmanaged model for Unity Bill records. PK transitioned to auto-increment 'id'.
    """
    # CRITICAL FIX: New Primary Key (Must exist in the database)
    id = models.AutoField(primary_key=True) 
    
    A_CCDatesMonth = models.DateField(db_column='A_CCDatesMonth') # No longer the PK
    B_Fund_Code = models.CharField(max_length=20, db_column='B_Fund_Code', null=True, blank=True)
    C_Company_Code = models.CharField(max_length=20, db_column='C_Company_Code', null=True, blank=True)
    D_Company_Name = models.CharField(max_length=255, db_column='D_Company_Name', null=True, blank=True)
    E_Active_Members = models.IntegerField(db_column='E_Active_Members', null=True, blank=True)
    
    # Scheduled/Billed Amounts
    F_Pre_Bill_Date = models.DateField(null=True, blank=True, db_column='F_Pre_Bill_Date')
    G_Schedule_Date = models.DateField(null=True, blank=True, db_column='G_Schedule_Date')
    H_Schedule_Amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column='H_Schedule_Amount')
    
    # Final Submission Fields (RETAINED)
    I_Submitted_Date = models.DateField(null=True, blank=True, db_column='I_Submitted_Date')
    J_Final_Date = models.DateField(null=True, blank=True, db_column='J_Final_Date')
    is_reconciled = models.BooleanField(default=False)
    
    # NOTE: K_ through T_ fields removed here.
    
    class Meta:
        managed = False 
        db_table = 'unity_bill'
        verbose_name = 'Unity Bill Record'

    def __str__(self):
        return f"Bill for {self.C_Company_Code} (ID: {self.id})"
    
# --- CORRECTED MODEL: ReconnedBank (CRITICAL FIXES APPLIED) ---
class ReconnedBank(models.Model):
    """
    Unmanaged model to store reconciliation results. Links to ImportBank.
    PK is now 'id' in MySQL, allowing multiple ReconnedBank segments per original ImportBank line (splitting).
    """
    # 1. NEW PRIMARY KEY (Matches the manually created 'id' column in MySQL)
    id = models.AutoField(primary_key=True) 

    # 2. Changed from OneToOneField (primary_key=True) to standard ForeignKey
    bank_line = models.ForeignKey(
        'ImportBank',
        on_delete=models.CASCADE,
        db_column='bank_line_id', # Explicitly map to the FK column in MySQL
        related_name='reconned_segments',
        verbose_name="Original Bank Line",
        # NOTE: If ImportBank had an explicit 'id' field, we'd use to_field='id'. Since ImportBank has 'id' as PK, this is implicit.
    )
    
    company_code = models.CharField(max_length=225)
    transaction_amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_date = models.DateField()
    
    fiscal_date = models.DateField(null=True, blank=True)
    review_note = models.CharField(max_length=255, null=True, blank=True)
    recon_status = models.CharField(max_length=50, default='Reconciled')
    
    # CRITICAL: Tracks how much of the original transaction_amount has been paid.
    amount_settled = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        null=False, 
        blank=False
    )
    
    # 3. REMOVED OBSOLETE FIELD: BillSettlement was dropped from MySQL.

    class Meta:
        managed = False
        db_table = 'reconned_bank'
        verbose_name = 'Reconciled Bank Line'

    def __str__(self):
        # Access bank_line ID directly via the FK
        return f"Recon {self.bank_line_id} segment {self.id} to {self.company_code}"

# User alias is defined at the top
# User = get_user_model() 

# --- CORRECTED MODEL: BillSettlement (FK Linkage to new ReconnedBank PK) ---
class BillSettlement(models.Model):
    """
    Unmanaged table linking a settled ReconnedBank line, Credit Note, or Surplus 
    to its UnityBill funding source. Now acts as the unified audit ledger.
    """
    id = models.AutoField(primary_key=True) 
    
    # 1. FK now targets the new 'id' PK of ReconnedBank.
    reconned_bank_line = models.ForeignKey(
        'ReconnedBank',
        on_delete=models.CASCADE,
        db_column='reconned_bank_line_id', 
        related_name='settlements',
        blank=True, 
        null=True,
    )
    
    # --- NEW FIELD FOR DIRECT AUDIT TRACEABILITY ---
    original_import_bank_id = models.IntegerField(
        db_column='original_import_bank_id',
        blank=True, 
        null=True,
        verbose_name='Original ImportBank ID'
    )
    # -----------------------------------------------
    
    unity_bill_source = models.ForeignKey(
        'UnityBill',
        on_delete=models.CASCADE,
        db_column='unity_bill_source_id',
        related_name='settled_lines',
    )
    
    settlement_date = models.DateTimeField() 
    settled_amount = models.DecimalField(max_digits=15, decimal_places=2) 

    # --- CRITICAL FIX: NEW AUDIT FIELDS (Confirmed by your schema) ---
    source_credit_note_id = models.IntegerField(
        db_column='source_credit_note_id', 
        blank=True, 
        null=True,
    )
    
    source_journal_entry_id = models.IntegerField(
        db_column='source_journal_entry_id', 
        blank=True, 
        null=True,
    )
    
    # 2. Confirmed by FK linkage in your bill_settlement table schema
    confirmed_by = models.ForeignKey(
        'auth.User', # Use 'auth.User' to refer to Django's built-in User model
        on_delete=models.SET_NULL,
        db_column='confirmed_by_id', # Explicitly match the column name from your schema
        null=True,
        blank=True,
        related_name='settled_bills',
        verbose_name='Confirmed By User'
    )

    class Meta:
        managed = False 
        db_table = 'bill_settlement'
        verbose_name = 'Bill Settlement'

    def __str__(self):
        return f"Settled R{self.settled_amount} for Bill {self.unity_bill_source.id}"

# --- NEW UNMANAGED MODEL: Pre_bill Staging (UNMANAGED) ---
class Pre_bill(models.Model):
    """
    Unmanaged staging table to temporarily store reconciled bank line data 
    before it is consolidated into a formal UnityBill record. 
    (Managed = False, as created directly in MySQL).
    """
    # Primary Key for the staging table itself
    id = models.AutoField(primary_key=True) 

    # Links directly to the ReconnedBank line that created this debt entry
    reconned_bank_line = models.ForeignKey(
        'ReconnedBank', 
        on_delete=models.CASCADE,
        db_column='reconned_bank_line_id', # Use the specific database column name
        verbose_name="Reconciled Bank Line Source"
    )

    # Data pulled from ReconnedBank
    company_code = models.CharField(max_length=225, verbose_name="Company Code")
    fiscal_date = models.DateField(null=True, blank=True, verbose_name="Fiscal Date")
    
    # Amount of the debt (pulled from ReconnedBank.transaction_amount)
    transaction_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Transaction Amount")
    
    # Date identified (pulled from ImportBank/ReconnedBank)
    date_identified = models.DateField(null=True, blank=True, verbose_name="Date Identified")

    # Tracking fields
    is_processed = models.BooleanField(default=False, verbose_name="Processed to UnityBill")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False 
        db_table = 'Pre_bill'
        verbose_name = 'Pre-Bill Staging Line'

    def __str__(self):
        return f"Pre-Bill Debt for {self.company_code} (Line ID: {self.reconned_bank_line_id})"
    
class CreditNote(models.Model):
    # Billing/Grouping Information
    ccdates_month = models.DateField(null=True, blank=True)
    fund_code = models.CharField(max_length=50, null=True, blank=True)
    member_group_code = models.CharField(max_length=50) # NOT NULL in SQL
    member_group_name = models.CharField(max_length=255, null=True, blank=True)
    active_members = models.IntegerField(null=True, blank=True)
    
    # Scheduling/Deposit Information
    schedule_date = models.DateField(null=True, blank=True)
    final_data_received_date = models.DateField(null=True, blank=True)
    schedule_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    confirmation_date = models.DateField(null=True, blank=True)
    bank_stmt_date = models.DateField(null=True, blank=True)
    bank_deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Review/Processing Fields
    comment = models.CharField(max_length=255, null=True, blank=True)
    receipt_in_live = models.CharField(max_length=50, null=True, blank=True)
    receipting_done_by = models.CharField(max_length=100, null=True, blank=True)
    balance_sufficient_flag = models.CharField(max_length=10, null=True, blank=True)
    date_letter_checked = models.DateField(null=True, blank=True)
    done_by = models.CharField(max_length=100, null=True, blank=True)

    # Import Metadata
    processed_date = models.DateTimeField(auto_now_add=True)
    processed_by = models.CharField(max_length=100)
    
    # --- NEW FIELDS FOR PROCESSING ---
    fiscal_date = models.DateField(null=True, blank=True)
    review_note = models.CharField(max_length=500, null=True, blank=True)

    # --- FOREIGN KEY TO UNITYBILL ---
    assigned_unity_bill = models.ForeignKey(
        'UnityBill', 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='applied_credit_notes'
    )

    class Meta:
        db_table = 'Credit_note' 
        managed = False
        
    def __str__(self):
        return f"Bill Data Import for {self.member_group_code} (R{self.schedule_amount})"
    
class ScheduleSurplus(models.Model):
    # Note: Using IntegerField for FKs since Django won't manage the constraints
    # 'id' is implied as the primary key if not explicitly listed with primary_key=True
    
    unity_bill_source_id = models.IntegerField(db_column='unity_bill_source_id')
    
    surplus_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        db_column='surplus_amount'
    )
    
    creation_date = models.DateField(db_column='creation_date', default=timezone.now)
    
    generating_credit_note_id = models.IntegerField(
        db_column='generating_credit_note_id',
        null=True,
        blank=True
    )
    
    status = models.CharField(
        max_length=20, 
        db_column='status',
        default='UNAPPLIED'
    )

    class Meta:
        # CRITICAL: Tells Django this table exists and shouldn't be managed by migrations.
        managed = False 
        db_table = 'unity_schedule_surplus'
        
    def __str__(self):
        return f"Surplus R{self.surplus_amount} from Bill ID {self.unity_bill_source_id} ({self.status})"
    
class JournalEntry(models.Model):
    """
    Represents an internal allocation of funds from a ScheduleSurplus 
    to an Open UnityBill within the SAME Company Code.
    """
    # Link to unity_schedule_surplus.id
    surplus_source = models.ForeignKey(
        'ScheduleSurplus', 
        on_delete=models.DO_NOTHING, # Safety for unmanaged DBs
        related_name='journal_allocations',
        db_column='surplus_source_id'
    )
    
    # Link to unity_bill.id
    target_bill = models.ForeignKey(
        'UnityBill', 
        on_delete=models.DO_NOTHING, 
        related_name='received_journal_entries',
        db_column='target_bill_id'
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    allocation_date = models.DateField(auto_now_add=True) # Django handles the date on save
    created_by = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        managed = False  # Django will NOT create/alter this table
        db_table = 'unity_journal_entry'

    def __str__(self):
        return f"Journal: R{self.amount} from Surplus #{self.surplus_source_id} to Bill #{self.target_bill_id}"
    
# --- OBSOLETE GMAIL MODELS (Kept for reference, but corresponding tables are dropped) ---

# NOTE: The models below were for the old Gmail API/Delegation flow.
# Since the MySQL tables were dropped, these models are now purely definitions, 
# but they are kept in the file as requested by your prompt.

class Unity_Internal_Inbox(models.Model):
    """ Master status table for incoming emails. (OBSOLETE GMAIL SCHEMA)"""
    email_id = models.CharField(max_length=255, primary_key=True)
    subject = models.CharField(max_length=512, null=True, blank=True)
    sender = models.CharField(max_length=255, null=True, blank=True)
    snippet = models.CharField(max_length=512, null=True, blank=True)
    received_timestamp = models.DateTimeField(default=timezone.now, null=True, blank=True)
    status = models.CharField(max_length=20, default='New')
    delegated_by = models.CharField(max_length=100, null=True, blank=True) 
    delegated_to = models.CharField(max_length=100, null=True, blank=True)
    work_related = models.CharField(max_length=5, default='Yes') 
    mip_number = models.CharField(max_length=20, null=True, blank=True)
    id_passport = models.CharField(max_length=50, null=True, blank=True)
    category = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=50, null=True, blank=True)
    method = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'unity_internal_inbox'
        verbose_name = 'Internal Inbox Status (OBSOLETE)'


class Unity_Internal_DelegateTo(models.Model):
    """ Stores full details of delegated tasks. (OBSOLETE GMAIL SCHEMA) """
    id = models.IntegerField(primary_key=True)
    email_id = models.CharField(max_length=255, unique=True)
    subject = models.CharField(max_length=512, null=True, blank=True)
    sender = models.CharField(max_length=255, null=True, blank=True)
    snippet = models.CharField(max_length=512, null=True, blank=True)
    received_timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default='New')
    delegated_by = models.CharField(max_length=100)
    delegated_to = models.CharField(max_length=100, null=True, blank=True)
    work_related = models.CharField(max_length=5, default='Yes') 
    mip_number = models.CharField(max_length=20, null=True, blank=True)
    id_passport = models.CharField(max_length=50, null=True, blank=True)
    category = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    method = models.CharField(max_length=50, null=True, blank=True)
    
    delegated_attachments = models.TextField(default='[]') 
    internal_notes = models.TextField(default='[]')

    class Meta:
        managed = False
        db_table = 'unity_internal_delegate_to'
        verbose_name = 'Internal Task Detail (OBSOLETE)'


class Unity_Internal_DelegateAction(models.Model):
    """ Audit log for actions taken on delegated tasks. (OBSOLETE GMAIL SCHEMA) """
    id = models.IntegerField(primary_key=True)
    task_email_id = models.CharField(max_length=255)
    action_type = models.CharField(max_length=50) 
    action_user = models.CharField(max_length=100)
    action_timestamp = models.DateTimeField(default=timezone.now)
    note_content = models.TextField(null=True, blank=True)
    related_subject = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'unity_internal_delegate_action'
        verbose_name = 'Internal Task Audit (OBSOLETE)'
        
# --- UNMANAGED EXTERNAL TABLE MODEL ---
class UnityNotes(models.Model):
    """
    Model for the UNMANAGED external 'unity_notes' table.
    """
    ID = models.IntegerField(primary_key=True) 
    member_group_code = models.TextField(db_column='Member Group Code')
    date = models.DateTimeField()
    user = models.TextField(db_column='User')
    notes = models.TextField()
    communication_type = models.CharField(max_length=90, db_column='Communication_Type')
    action_notes = models.CharField(max_length=90, db_column='Action_Notes')

    class Meta:
        db_table = 'unity_notes'
        managed = False
        verbose_name_plural = "Unity Notes"
        
class UnityClaim(models.Model):
    # --- Dropdown Choices ---
    CLAIM_TYPES = [
        ('Retirement', 'Retirement'), ('Withdrawal', 'Withdrawal'), ('Death', 'Death'), 
        ('Disability', 'Disability'), ('Funeral', 'Funeral'), ('Surplus', 'Surplus'), 
        ('Ill-Health', 'Ill-Health'),
    ]

    EXIT_REASONS = [
        ('Resignation', 'Resignation'), ('Dismissal', 'Dismissal'), ('Retirement', 'Retirement'), 
        ('Retrenchment', 'Retrenchment'), ('Death', 'Death'), ('Disability', 'Disability'), 
        ('Funeral', 'Funeral'), ('Ill-Health', 'Ill-Health'), ('Abscondment', 'Abscondment'),
    ]

    ALLOCATION_STATUS = [
        ('New Claim', 'New Claim'), ('Dealing With Claim', 'Dealing With Claim'), 
        ('Claim Query', 'Claim Query'), ('Claim Paid', 'Claim Paid'), 
        ('Exit Processed', 'Exit Processed'),
    ]

    CLAIM_STATUS = [
        ('Claim Docs Requested', 'Claim Docs Requested'), ('Delegated', 'Delegated'), 
        ('Incomplete', 'Incomplete'), ('Paid', 'Paid'), ('Submitted', 'Submitted'), 
        ('Company in Arrears', 'Company in Arrears'), ('Payment/Schedule Due', 'Payment/Schedule Due'), 
        ('Completed', 'Completed'), ('Family Member – Sent to Sanlam', 'Family Member – Sent to Sanlam'),
    ]

    PAYMENT_OPTIONS = [
        ('Leave Benefit in Fund', 'Leave Benefit in Fund'), ('Transfer Full Benefit', 'Transfer Full Benefit'), 
        ('Portion Cash and Transfer Balance', 'Portion Cash and Transfer Balance'), 
        ('Pay Full Benefit', 'Pay Full Benefit'), ('No Payment Instruction', 'No Payment Instruction'),
    ]

    # --- Database Fields ---
    company_code = models.CharField(max_length=50, db_index=True) 
    agent = models.CharField(max_length=100, blank=True, null=True)
    
    id_number = models.CharField(max_length=20)
    member_name = models.CharField(max_length=100)
    member_surname = models.CharField(max_length=100)
    
    claim_type = models.CharField(max_length=50, choices=CLAIM_TYPES, default='Withdrawal')
    exit_reason = models.CharField(max_length=50, choices=EXIT_REASONS, blank=True, null=True)
    claim_allocation = models.CharField(max_length=50, choices=ALLOCATION_STATUS, default='New Claim')
    claim_status = models.CharField(max_length=50, choices=CLAIM_STATUS, default='Claim Docs Requested')
    payment_option = models.CharField(max_length=50, choices=PAYMENT_OPTIONS, blank=True, null=True)
    
    claim_created_date = models.DateField() 
    last_contribution_date = models.DateField(blank=True, null=True)
    date_submitted = models.DateField(blank=True, null=True)
    date_paid = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'unity_claims'
        ordering = ['-last_contribution_date', 'member_surname']
        verbose_name = "Company Claim"
        verbose_name_plural = "Company Claims"

    def __str__(self):
        return f"{self.member_surname}, {self.member_name} ({self.company_code})"
    
# NOTE: User is already imported via get_user_model() at the top
# from django.contrib.auth.models import User 
    
class UnityClaimNote(models.Model):
    claim = models.ForeignKey(UnityClaim, on_delete=models.CASCADE, related_name='notes')
    note_selection = models.CharField(max_length=255, blank=True, null=True)
    note_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Note for Claim {self.claim.id} - {self.created_at}"
    
class Unity_Internal_OutgoingEmail(models.Model):
    """ Stores direct outgoing emails sent from the Unity Dashboard. (OBSOLETE GMAIL SCHEMA) """
    member_group_code = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    sender_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    recipient_email = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body_html = models.TextField(blank=True, null=True)
    sent_timestamp = models.DateTimeField(auto_now_add=True)
    gmail_message_id = models.CharField(max_length=100, blank=True, null=True, help_text="The Gmail ID returned by the API")
    attachments_metadata = models.TextField(blank=True, null=True, help_text="JSON string of attachment names")

    class Meta:
        db_table = 'unity_internal_outgoing_email'
        managed = False # Keeping this explicit for consistency
        ordering = ['-sent_timestamp']

    def __str__(self):
        return f"{self.subject} (To: {self.recipient_email})"

# =========================================================================
# --- START OF NEW GRAPH API & DELEGATION MODELS (Managed by Django) ---
# =========================================================================

# 1. Token Storage (Required by token_manager.py)
class OutlookToken(models.Model):
    """Stores the single Client Credentials token for the delegated mailbox."""
    user_principal_name = models.CharField(max_length=255, primary_key=True)
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    expires_in_seconds = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True) # auto_now ensures updated_at is correct for expiry calculation

    class Meta:
        # Django will automatically name this table 'unity_internal_outlooktoken'
        app_label = 'unity_internal' 
        verbose_name = 'Graph Access Token'

# 2. Email Delegation Status (Required by delegation_service.py)
class EmailDelegation(models.Model):
    """The master status table for an email task."""
    email_id = models.CharField(max_length=255, unique=True)
    
    # ForeignKey links to the standard Django User table
    assigned_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='delegated_tasks')
    
    # Status and Date Fields
    STATUS_CHOICES = [
        ('NEW', 'Undelegated - New'),
        ('DEL', 'Delegated'),
        ('COM', 'Completed'),
        ('RED', 'Re-delegated'),
    ]
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='NEW')
    delegated_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    
    # Classification Fields (from ACVV logic)
    company_code = models.CharField(max_length=255, null=True, blank=True) # <-- CORRECTED FIELD NAME
    email_category = models.CharField(max_length=50, null=True, blank=True)
    work_related = models.BooleanField(default=True)
    communication_type = models.CharField(max_length=50, null=True, blank=True)
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    class Meta:
        # Django will automatically name this table 'unity_internal_emaildelegation'
        app_label = 'unity_internal'
        verbose_name = 'Delegation Task'

# 3. Delegation Note (Required by delegation_service.py)
class DelegationNote(models.Model):
    """Internal notes against a delegated task."""
    # ForeignKey uses the new EmailDelegation model
    delegation = models.ForeignKey(EmailDelegation, on_delete=models.CASCADE, related_name='notes')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Django will automatically name this table 'unity_internal_delegationnote'
        app_label = 'unity_internal'
        verbose_name = 'Delegation Note'
        ordering = ['-created_at']


# 4. Delegation Transaction Log (Required by delegation_service.py)
class DelegationTransactionLog(models.Model):
    """Audit log for actions taken on a delegated task (e.g., email reply)."""
    # ForeignKey uses the new EmailDelegation model
    delegation = models.ForeignKey(EmailDelegation, on_delete=models.CASCADE, related_name='transactions')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=50) # e.g., 'EMAIL_REPLY', 'TASK_COMPLETE'
    subject = models.CharField(max_length=255)
    recipient_email = models.EmailField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Django will automatically name this table 'unity_internal_delegationtransactionlog'
        app_label = 'unity_internal'
        verbose_name = 'Delegation Transaction Log'
        ordering = ['-timestamp']