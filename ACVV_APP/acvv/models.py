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
    assigned_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        # Default name is acvv_user_id, setting for clarity if needed
    )
    
    STATUS_CHOICES = [
        ('NEW', 'Undelegated - New'),
        ('DEL', 'Delegated'),
        ('COM', 'Completed'),
        ('CLO', 'Closed')
    ]
    status = models.CharField(
        max_length=3,
        choices=STATUS_CHOICES,
        default='NEW'
    )
    
    received_at = models.DateTimeField(null=True, blank=True)
    delegated_at = models.DateTimeField(null=True, blank=True)
    
    # 🛑 NEW CLASSIFICATION FIELDS 🛑
    work_related = models.BooleanField(default=True) # Assuming defaults to Yes
    email_category = models.CharField(max_length=50, null=True, blank=True)
    communication_type = models.CharField(max_length=50, null=True, blank=True)
    mip_names = models.CharField(max_length=50, null=True, blank=True) # For MIP/Group Code

    def __str__(self):
        return f"Task ID {self.pk} - {self.get_status_display()}"

    class Meta:
        # 🛑 CRITICAL: Tell Django not to manage the schema
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