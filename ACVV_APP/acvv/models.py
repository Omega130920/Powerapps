from django.db import models
from django.contrib.auth.models import User

class Globalacvv(models.Model):
    """
    Model representing the 'global acvv' table.
    """
    mip_names = models.CharField(db_column='MIP Names', max_length=255, primary_key=True)
    branch_code = models.CharField(db_column='Branch Code', max_length=255, null=True, blank=True)
    member = models.CharField(db_column='MEMBER', max_length=255, null=True, blank=True)
    status = models.CharField(db_column='STATUS', max_length=255, null=True, blank=True)
    contribution_amount = models.CharField(db_column='CONTRIBUTION AMOUNT', max_length=255, null=True, blank=True)
    notes = models.CharField(db_column='NOTES', max_length=255, null=True, blank=True)
    schedule_date_received = models.CharField(db_column='SCHEDULE DATE RECEIVED', max_length=255, null=True, blank=True)
    deb_order_date_confirm = models.CharField(db_column='DEB ORDER DATE CONFIRM BY EMPOLYER(FUND)', max_length=255, null=True, blank=True)
    bank_info_upload = models.CharField(db_column='Bank info Upload', max_length=225, null=True, blank=True)
    mg_email_address = models.CharField(db_column='MG EMAIL ADDRESS', max_length=225, null=True, blank=True)
    tel = models.CharField(db_column='TEL', max_length=20, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'global acvv'

class ClientNotes(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)
    # Change this field to a ForeignKey
    acvv_record = models.ForeignKey(
        'Globalacvv', 
        on_delete=models.CASCADE, 
        db_column='MIP Names', 
        to_field='mip_names'
    )
    date = models.DateTimeField(db_column='Date', null=True, blank=True)
    user = models.TextField(db_column='User', null=True, blank=True)
    notes = models.TextField(db_column='Notes', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'client_notes'
        
from django.db import models

class OutlookToken(models.Model):
    """
    Stores the Access Token and Refresh Token for the managed Outlook account.
    This model is UNMANAGED, meaning Django will not create, modify, or delete 
    the corresponding database table.
    """
    # The identifier for the user (can be the email address)
    user_principal_name = models.CharField(max_length=255, unique=True)
    
    # The actual token used to call the Graph API
    access_token = models.TextField()
    
    # The token used to request a new Access Token
    refresh_token = models.TextField(null=True, blank=True)
    
    # When the Access Token expires (in seconds, used for proactive refresh)
    expires_in_seconds = models.IntegerField(default=3600) 
    
    # Timestamp of when the token record was last updated
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        # 🛑 Set managed to False so Django migrations ignore this model 🛑
        managed = False
        db_table = 'acvv_outlook_token' # Optional: Define the exact table name for clarity

    def __str__(self):
        return f"Token for {self.user_principal_name}"
    
# ----------------------------------------------------------------------
# NEW UNMANAGED MODELS FOR DELEGATION
# ----------------------------------------------------------------------

class EmailDelegation(models.Model):
    """Tracks delegation status, assignee, notes, and classification for a specific Outlook email."""
    
    email_id = models.CharField(max_length=255, unique=True)
    subject = models.CharField(max_length=255, null=True, blank=True) # 🛑 NEW FIELD
    assigned_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
    )
    
    STATUS_CHOICES = [
        ('NEW', 'Undelegated - New'),
        ('DEL', 'Delegated'),
        ('COM', 'Completed'),
        ('CLO', 'Closed'),
        ('DLT', 'Deleted'), 
    ]
    
    status = models.CharField(
        max_length=3,
        choices=STATUS_CHOICES,
        default='NEW'
    )
    
    received_at = models.DateTimeField(null=True, blank=True)
    delegated_at = models.DateTimeField(null=True, blank=True)
    sender_address = models.CharField(max_length=255, null=True, blank=True)
    
    work_related = models.BooleanField(default=True)
    email_category = models.CharField(max_length=50, null=True, blank=True)
    communication_type = models.CharField(max_length=50, null=True, blank=True)
    mip_names = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Task ID {self.pk} - {self.get_status_display()}"

    class Meta:
        managed = False
        db_table = 'email_delegation'

class DelegationNote(models.Model):
    """Notes added by the assigned user against a delegated email."""
    
    delegation = models.ForeignKey(
        EmailDelegation, 
        on_delete=models.CASCADE,
        related_name='notes'
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # 🛑 CRITICAL: Tell Django not to manage the schema
        managed = False
        db_table = 'delegation_note'
        ordering = ['created_at']
        
class DelegationTransactionLog(models.Model):
    """Logs external communication events (like email replies) against a task."""
    
    delegation = models.ForeignKey(
        EmailDelegation, 
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    subject = models.CharField(max_length=255)
    recipient_email = models.CharField(max_length=255)
    action_type = models.CharField(max_length=50) # Use constants like 'EMAIL_REPLY'
    
    transaction_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'delegation_transaction_log' 
        ordering = ['transaction_time']
        
class AcvvClaim(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)
    company_code = models.CharField(db_column='company_code', max_length=50) 
    agent = models.CharField(db_column='agent', max_length=100, null=True, blank=True)
    id_number = models.CharField(db_column='id_number', max_length=50)
    member_name = models.CharField(db_column='member_name', max_length=255)
    member_surname = models.CharField(db_column='member_surname', max_length=255)
    mip_number = models.CharField(db_column='mip_number', max_length=50, null=True, blank=True)
    claim_type = models.CharField(db_column='claim_type', max_length=100)
    exit_reason = models.CharField(db_column='exit_reason', max_length=100, null=True, blank=True)
    claim_allocation = models.CharField(db_column='claim_allocation', max_length=100)
    claim_status = models.CharField(db_column='claim_status', max_length=100)
    payment_option = models.CharField(db_column='payment_option', max_length=100, null=True, blank=True)
    claim_amount = models.DecimalField(db_column='claim_amount', max_digits=15, decimal_places=2, null=True, blank=True)
    
    claim_created_date = models.DateField(db_column='claim_created_date', null=True, blank=True)
    last_contribution_date = models.DateField(db_column='last_contribution_date', null=True, blank=True)
    date_submitted = models.DateField(db_column='date_submitted', null=True, blank=True)
    date_paid = models.DateField(db_column='date_paid', null=True, blank=True)
    
    vested_pot_available = models.BooleanField(db_column='vested_pot_available', default=False)
    vested_pot_paid_date = models.DateField(db_column='vested_pot_paid_date', null=True, blank=True)
    savings_pot_available = models.BooleanField(db_column='savings_pot_available', default=False)
    savings_pot_paid_date = models.DateField(db_column='savings_pot_paid_date', null=True, blank=True)
    infund_cert_date = models.DateField(db_column='infund_cert_date', null=True, blank=True)
    
    linked_email_id = models.CharField(db_column='linked_email_id', max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'acvv_claims'

class ClaimNote(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)
    claim = models.ForeignKey(AcvvClaim, on_delete=models.CASCADE, related_name='notes', db_column='claim_id')
    note_selection = models.CharField(db_column='note_selection', max_length=255, null=True, blank=True)
    note_description = models.TextField(db_column='note_description', null=True, blank=True)
    attachment = models.FileField(db_column='attachment', upload_to='claim_attachments/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(db_column='created_at', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_column='created_by_id')

    class Meta:
        managed = False
        db_table = 'acvv_claim_notes'
        
class ReconciliationRecord(models.Model):
    """Stores fiscal month data for branch reconciliations (8th to 7th cycle)."""
    fiscal_month = models.DateField()
    mip_name = models.CharField(max_length=255)
    branch_code = models.CharField(max_length=50)
    
    billed_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    outstanding_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    note = models.TextField(null=True, blank=True)
    
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False  # Set to False as per your requirement
        db_table = 'reconciliation_record'

    def __str__(self):
        return f"{self.mip_name} - {self.fiscal_month.strftime('%B %Y')}"
    
class ReconciliationWorksheet(models.Model):
    fiscal_month = models.DateField()
    mg_name = models.CharField(max_length=255)
    mg_code = models.CharField(max_length=100)
    company_status = models.CharField(max_length=50, default='Active')
    payment_method = models.CharField(max_length=50, default='Debit Order')
    last_fiscal_reconciled = models.CharField(max_length=100, null=True, blank=True)
    arrears = models.CharField(max_length=255, null=True, blank=True)
    member_count_reconciled = models.IntegerField(default=0)
    contribution_amount_reconciled = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    reconciled_status = models.CharField(max_length=50, default='Unreconciled')
    date_schedule_received = models.DateField(null=True, blank=True)
    date_confirmed_on_step = models.DateField(null=True, blank=True)
    debit_order_date = models.DateField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'reconciliation_worksheet'