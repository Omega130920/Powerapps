from django.db import models

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
    email_category = models.CharField(max_length=100, blank=True, null=True) # Added
    subject = models.CharField(max_length=255, blank=True, null=True)        # Added
    sender = models.CharField(max_length=255, blank=True, null=True)         # Added
    status = models.CharField(max_length=50, default='Assigned')
    created_at = models.DateTimeField(auto_now_add=True)

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