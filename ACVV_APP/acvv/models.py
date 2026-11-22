from django.db import models
from django.contrib.auth.models import User


class Globalacvv(models.Model):
    # Existing fields
    mip_names = models.CharField(db_column='MIP Names', max_length=255, primary_key=True)
    branch_code = models.CharField(db_column='Branch Code', max_length=255, null=True, blank=True)
    member = models.CharField(db_column='MEMBER', max_length=255, null=True, blank=True)
    status = models.CharField(db_column='STATUS', max_length=255, null=True, blank=True)
    contribution_amount = models.CharField(db_column='CONTRIBUTION AMOUNT', max_length=255, null=True, blank=True)
    notes = models.CharField(db_column='NOTES', max_length=255, null=True, blank=True)
    schedule_date_received = models.CharField(db_column='SCHEDULE DATE RECEIVED', max_length=255, null=True, blank=True)
    deb_order_confirm = models.CharField(db_column='DEB ORDER DATE CONFIRM BY EMPOLYER(FUND)', max_length=255, null=True, blank=True)
    bank_info_upload = models.CharField(db_column='Bank info Upload', max_length=225, null=True, blank=True)
    mg_email_address = models.CharField(db_column='MG EMAIL ADDRESS', max_length=225, null=True, blank=True)
    
    # Primary Telephone
    tel = models.CharField(db_column='TEL', max_length=50, null=True, blank=True)
    
    # Secondary Telephone
    tel_2 = models.CharField(db_column='TEL 2', max_length=50, null=True, blank=True)

    # --- NEW BANK & EMPLOYER CONTACT FIELDS ---
    bank = models.CharField(db_column='BANK', max_length=255, null=True, blank=True)
    branch = models.CharField(db_column='BRANCH', max_length=255, null=True, blank=True)
    account_number = models.CharField(db_column='ACCOUNT NUMBER', max_length=255, null=True, blank=True)
    account_name = models.CharField(db_column='ACCOUNT NAME', max_length=255, null=True, blank=True)
    account_type = models.CharField(db_column='ACCOUNT TYPE', max_length=255, null=True, blank=True)
    employer_contacts = models.CharField(db_column='EMPLOYER CONTACTS', max_length=255, null=True, blank=True)

    # Address, NPO Code & Bank Info
    mg_address = models.CharField(db_column='MG ADDRESS', max_length=255, null=True, blank=True)
    npo_code = models.CharField(db_column='NPO CODE', max_length=100, null=True, blank=True)
    mg_bank_info = models.CharField(db_column='MG BANK INFO', max_length=255, null=True, blank=True)

    class Meta:
        managed = False  # Set to False because you manage the schema manually in MySQL
        db_table = 'global acvv'  # Explicitly using the name with the space

    def __str__(self):
        return self.mip_names


class ClientNotes(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)
    # Mapping to 'MIP Names' column
    acvv_record = models.ForeignKey(
        'Globalacvv', 
        on_delete=models.CASCADE, 
        db_column='MIP Names', 
        to_field='mip_names'
    )
    date = models.DateTimeField(db_column='date', null=True, blank=True)
    user = models.TextField(db_column='User', null=True, blank=True)
    notes = models.TextField(db_column='notes', null=True, blank=True)

    # New columns matching your schema
    communication_type = models.CharField(
        db_column='communication_type', 
        max_length=100, 
        null=True, 
        blank=True
    )
    action_note_type = models.CharField(
        db_column='action_note_type', 
        max_length=100, 
        null=True, 
        blank=True
    )
    # Using FileField to manage the varchar(255) path
    attachment = models.FileField(
        db_column='attachment', 
        upload_to='notes_attachments/', 
        max_length=255, 
        null=True, 
        blank=True
    )

    class Meta:
        managed = False
        db_table = 'client_notes'


class OutlookToken(models.Model):
    """
    Stores the Access Token and Refresh Token for the managed Outlook account.
    This model is UNMANAGED, meaning Django will not create, modify, or delete 
    the corresponding database table.
    """
    user_principal_name = models.CharField(max_length=255, unique=True)
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    expires_in_seconds = models.IntegerField(default=3600) 
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        managed = False
        db_table = 'acvv_outlook_token'

    def __str__(self):
        return f"Token for {self.user_principal_name}"


# ----------------------------------------------------------------------
# UNMANAGED MODELS FOR DELEGATION & LOCAL EMAIL STORAGE
# ----------------------------------------------------------------------

class EmailDelegation(models.Model):
    """Tracks delegation status, assignee, full local email content, and classification for an Outlook email."""
    
    email_id = models.CharField(max_length=255, unique=True, db_collation='utf8mb4_bin')
    subject = models.CharField(max_length=255, null=True, blank=True)
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
        ('SENT', 'Sent Direct'),
    ]
    
    status = models.CharField(
        max_length=4,
        choices=STATUS_CHOICES,
        default='NEW'
    )
    
    received_at = models.DateTimeField(null=True, blank=True)
    delegated_at = models.DateTimeField(null=True, blank=True)
    sender_address = models.CharField(max_length=255, null=True, blank=True)
    sender_name = models.CharField(max_length=255, null=True, blank=True)
    snippet = models.CharField(max_length=512, null=True, blank=True)
    to_recipients = models.TextField(null=True, blank=True)
    cc_recipients = models.TextField(null=True, blank=True)
    bcc_recipients = models.TextField(null=True, blank=True)
    
    work_related = models.BooleanField(default=True)
    email_category = models.CharField(max_length=50, null=True, blank=True)
    communication_type = models.CharField(max_length=50, null=True, blank=True)
    mip_names = models.CharField(max_length=255, null=True, blank=True)

    # Local rendering, attachment & .eml archive fields
    body = models.TextField(null=True, blank=True)
    has_attachments = models.BooleanField(default=False)
    eml_file_path = models.CharField(max_length=500, null=True, blank=True)
    is_fully_synced = models.BooleanField(default=False)
    attachment = models.FileField(
        upload_to='email_attachments/%Y/%m/', 
        max_length=255, 
        null=True, 
        blank=True
    )

    def __str__(self):
        return f"Task ID {self.pk} - {self.get_status_display()}"

    class Meta:
        managed = False
        db_table = 'email_delegation'


class AcvvEmailAttachment(models.Model):
    """Stores locally downloaded incoming, inline CID, reply, and direct/claim email attachments on disk."""
    
    id = models.AutoField(primary_key=True)
    email_id = models.CharField(max_length=255, db_index=True, db_collation='utf8mb4_bin')
    attachment_id = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=150, null=True, blank=True)
    size = models.IntegerField(default=0)
    is_inline = models.BooleanField(default=False)
    content_id = models.CharField(max_length=255, null=True, blank=True)
    file_path = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'acvv_email_attachments'

    def __str__(self):
        return f"{self.name} ({self.email_id})"


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
    cc_recipients = models.TextField(null=True, blank=True)
    bcc_recipients = models.TextField(null=True, blank=True)
    action_type = models.CharField(max_length=50)
    
    body = models.TextField(null=True, blank=True)
    eml_file_path = models.CharField(max_length=500, null=True, blank=True)
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

    # --- DYNAMIC PROPERTIES (NO DATABASE MIGRATION REQUIRED) ---
    
    @property
    def qualified(self):
        latest_note = self.notes.order_by('-created_at').first()
        if latest_note and "[Tracking Parameters Logged]" in (latest_note.note_description or ""):
            if "- Qualified: NO" in latest_note.note_description:
                return "NO"
        return "YES"

    @property
    def informed_er(self):
        latest_note = self.notes.order_by('-created_at').first()
        if latest_note and "[Tracking Parameters Logged]" in (latest_note.note_description or ""):
            if "- Informed ER: YES" in latest_note.note_description:
                return "YES"
        return "NO"

    @property
    def submitted_by_agent(self):
        latest_note = self.notes.order_by('-created_at').first()
        if latest_note and "[Tracking Parameters Logged]" in (latest_note.note_description or ""):
            import re
            match = re.search(r"- Submitted by Agent: (\w+)", latest_note.note_description)
            if match:
                return match.group(1)
        return ""


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
        managed = False  
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
    
    lpi_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    lpi_reason = models.CharField(max_length=100, null=True, blank=True)
    debit_order_success = models.CharField(max_length=10, null=True, blank=True)

    reconciled_status = models.CharField(max_length=50, default='Unreconciled')
    date_schedule_received = models.DateField(null=True, blank=True)
    date_confirmed_on_step = models.DateField(null=True, blank=True)
    debit_order_date = models.DateField(null=True, blank=True)
    
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)

    # --- SLA & AUDIT FIELDS ---
    updated_at = models.DateTimeField(auto_now=True) 
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'reconciliation_worksheet'
        unique_together = (('mg_code', 'fiscal_month'),)

    def __str__(self):
        return f"{self.mg_code} - {self.fiscal_month}"


class BranchDocument(models.Model):
    branch_name = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'branch_documents'


class TempExit(models.Model):
    mg_code = models.CharField(max_length=50)
    surname = models.CharField(max_length=255)
    initials = models.CharField(max_length=50, null=True, blank=True)
    mip_no = models.CharField(max_length=100, null=True, blank=True)
    id_no = models.CharField(max_length=13, null=True, blank=True)
    reason = models.CharField(max_length=255, null=True, blank=True)
    bis_from_date = models.DateField(null=True, blank=True)
    bis_end_date = models.DateField(null=True, blank=True)
    full_contributions_start_date = models.DateField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'temp_exit'