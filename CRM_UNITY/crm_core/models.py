from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

# ==============================================================================
# NEW: MICROSOFT GRAPH TOKEN STORAGE (UNMANAGED)
# ==============================================================================

class CrmUnityOutlookToken(models.Model):
    """
    Stores Microsoft Graph OAuth tokens. 
    Managed = False: Table must be created via raw SQL in MySQL.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='outlook_token')
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'crm_unity_outlooktoken'

# ==============================================================================
# CORE CRM CONTACT TABLES (UNMANAGED)
# ==============================================================================

class GlobalFundContact(models.Model):
    member_group_code = models.CharField(db_column='Member_Group_Code', max_length=255, primary_key=True)
    member_group_name = models.CharField(db_column='Member_Group_Name', max_length=255, null=True, blank=True)
    commencement_date = models.DateField(db_column='Commencement_Date', null=True, blank=True)
    fund_status = models.CharField(db_column='Fund_status', max_length=255, null=True, blank=True)
    business_postal_address = models.CharField(db_column='Business_Postal_Address', max_length=255, null=True, blank=True)
    business_postal_address_post_code = models.CharField(db_column='Business_Postal_address_post_Code', max_length=255, null=True, blank=True)
    business_physical_address2 = models.CharField(db_column='Business_Physical_Address2', max_length=255, null=True, blank=True)
    business_physical_address_post_code2 = models.CharField(db_column='Business_Physical_address_post_code2', max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'global_fund_contact_list'

class Cbc(models.Model):
    member_group_code = models.CharField(db_column='Member_Group_Code', max_length=255, primary_key=True)
    title = models.CharField(db_column='Title', max_length=255, null=True, blank=True)
    first_name = models.CharField(db_column='First_Name', max_length=255, null=True, blank=True)
    surname = models.CharField(db_column='Surname', max_length=255, null=True, blank=True)
    id_number = models.CharField(db_column='ID_Number', max_length=255, null=True, blank=True)
    email_address = models.CharField(db_column='Email_Address', max_length=255, null=True, blank=True)
    indemnity = models.CharField(db_column='Indemnity', max_length=225, null=True, blank=True)
    work_dial_code = models.CharField(db_column='Work_Dial_Code', max_length=10, null=True, blank=True)
    work_contact_number = models.CharField(db_column='Work_Contact_Number', max_length=255, null=True, blank=True)
    fax_dial_code = models.CharField(db_column='Fax_Dial_Code', max_length=10, null=True, blank=True)
    fax_number = models.CharField(db_column='Fax_Number', max_length=255, null=True, blank=True)
    mobile_number = models.CharField(db_column='Mobile_Number', max_length=255, null=True, blank=True)
    business_postal_address = models.CharField(db_column='Business_Postal_address', max_length=255, null=True, blank=True)
    post_code = models.CharField(db_column='Post_Code', max_length=10, null=True, blank=True)
    business_physical_address = models.CharField(db_column='Business_Physical_address', max_length=255, null=True, blank=True)
    post_code2 = models.CharField(db_column='Post_Code2', max_length=10, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'cbc'

class CbcAdminPerson(models.Model):
    member_group_code = models.CharField(db_column='Member_Group_Code', max_length=255, primary_key=True)
    title = models.CharField(db_column='Title', max_length=255, null=True, blank=True)
    first_name = models.CharField(db_column='First_Name', max_length=255, null=True, blank=True)
    surname = models.CharField(db_column='Surname', max_length=255, null=True, blank=True)
    id_number = models.CharField(db_column='ID_Number', max_length=255, null=True, blank=True)
    email_address = models.CharField(db_column='Email_Address', max_length=255, null=True, blank=True)
    work_dial_code = models.CharField(db_column='Work_Dial_Code', max_length=10, null=True, blank=True)
    work_contact_number = models.CharField(db_column='Work_Contact_Number', max_length=255, null=True, blank=True)
    fax_dial_code = models.CharField(db_column='Fax_Dial_Code', max_length=10, null=True, blank=True)
    fax_number = models.CharField(db_column='Fax_Number', max_length=255, null=True, blank=True)
    mobile_number = models.CharField(db_column='Mobile_Number', max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'cbc_admin_person'

class CbcConsultancyPerson(models.Model):
    member_group_code = models.CharField(db_column='Member_Group_Code', max_length=255, primary_key=True)
    title = models.CharField(db_column='Title', max_length=255, null=True, blank=True)
    first_name = models.CharField(db_column='First_Name', max_length=255, null=True, blank=True)
    surname = models.CharField(db_column='Surname', max_length=255, null=True, blank=True)
    id_number = models.CharField(db_column='ID_Number', max_length=255, null=True, blank=True)
    email_address = models.CharField(db_column='Email_Address', max_length=255, null=True, blank=True)
    work_dial_code = models.CharField(db_column='Work_Dial_Code', max_length=10, null=True, blank=True)
    work_contact_number = models.CharField(db_column='Work_Contact_Number', max_length=255, null=True, blank=True)
    fax_dial_code = models.CharField(db_column='Fax_Dial_Code', max_length=10, null=True, blank=True)
    fax_number = models.CharField(db_column='Fax_Number', max_length=255, null=True, blank=True)
    mobile_number = models.CharField(db_column='Mobile_Number', max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'cbc_consultancy_person'

class Cfa(models.Model):
    member_group_code = models.CharField(db_column='Member_Group_Code', max_length=255, primary_key=True)
    title = models.CharField(db_column='Title', max_length=255, null=True, blank=True)
    first_name = models.CharField(db_column='First_Name', max_length=255, null=True, blank=True)
    surname = models.CharField(db_column='Surname', max_length=255, null=True, blank=True)
    id_number = models.CharField(db_column='ID_Number', max_length=255, null=True, blank=True)
    email_address = models.CharField(db_column='Email_Address', max_length=255, null=True, blank=True)
    work_dial_code = models.CharField(db_column='Work_Dial_Code', max_length=10, null=True, blank=True)
    work_contact_number = models.CharField(db_column='Work_Contact_Number', max_length=255, null=True, blank=True)
    fax_dial_code = models.CharField(db_column='Fax_Dial_Code', max_length=10, null=True, blank=True)
    fax_number = models.CharField(db_column='Fax_Number', max_length=255, null=True, blank=True)
    mobile_number = models.CharField(db_column='Mobile_Number', max_length=255, null=True, blank=True)
    business_postal_address = models.CharField(db_column='Business_Postal_address', max_length=255, null=True, blank=True)
    post_code = models.CharField(db_column='Post_Code', max_length=10, null=True, blank=True)
    business_physical_address = models.CharField(db_column='Business_Physical_address', max_length=255, null=True, blank=True)
    post_code2 = models.CharField(db_column='Post_Code2', max_length=10, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'cfa'

class CfaAdminPerson(models.Model):
    member_group_code = models.CharField(db_column='Member_Group_Code', max_length=255, primary_key=True)
    title = models.CharField(db_column='Title', max_length=255, null=True, blank=True)
    first_name = models.CharField(db_column='First_Name', max_length=255, null=True, blank=True)
    surname = models.CharField(db_column='Surname', max_length=255, null=True, blank=True)
    id_number = models.CharField(db_column='ID_Number', max_length=255, null=True, blank=True)
    email_address = models.CharField(db_column='Email_Address', max_length=255, null=True, blank=True)
    work_dial_code = models.CharField(db_column='Work_Dial_Code', max_length=10, null=True, blank=True)
    work_contact_number = models.CharField(db_column='Work_Contact_Number', max_length=255, null=True, blank=True)
    fax_dial_code = models.CharField(db_column='Fax_Dial_Code', max_length=10, null=True, blank=True)
    fax_number = models.CharField(db_column='Fax_Number', max_length=255, null=True, blank=True)
    mobile_number = models.CharField(db_column='Mobile_Number', max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'cfa_admin_person'

class Cfa2(models.Model):
    member_group_code = models.CharField(db_column='Member_Group_Code', max_length=255, primary_key=True)
    title = models.CharField(db_column='Title', max_length=255, null=True, blank=True)
    first_name = models.CharField(db_column='First_Name', max_length=255, null=True, blank=True)
    surname = models.CharField(db_column='Surname', max_length=255, null=True, blank=True)
    id_number = models.CharField(db_column='ID_Number', max_length=255, null=True, blank=True)
    email_address = models.CharField(db_column='Email_Address', max_length=255, null=True, blank=True)
    work_dial_code = models.CharField(db_column='Work_Dial_Code', max_length=10, null=True, blank=True)
    work_contact_number = models.CharField(db_column='Work_Contact_Number', max_length=255, null=True, blank=True)
    fax_dial_code = models.CharField(db_column='Fax_Dial_Code', max_length=10, null=True, blank=True)
    fax_number = models.CharField(db_column='Fax_Number', max_length=255, null=True, blank=True)
    mobile_number = models.CharField(db_column='Mobile_Number', max_length=255, null=True, blank=True)
    business_postal_address = models.CharField(db_column='Business_Postal_address', max_length=255, null=True, blank=True)
    post_code = models.CharField(db_column='Post_Code', max_length=10, null=True, blank=True)
    business_physical_address = models.CharField(db_column='Business_Physical_address', max_length=255, null=True, blank=True)
    post_code2 = models.CharField(db_column='Post_Code2', max_length=10, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'cfa2'

class Cfa3(models.Model):
    member_group_code = models.CharField(db_column='Member_Group_Code', max_length=255, primary_key=True)
    title = models.CharField(db_column='Title', max_length=255, null=True, blank=True)
    first_name = models.CharField(db_column='First_Name', max_length=255, null=True, blank=True)
    surname = models.CharField(db_column='Surname', max_length=255, null=True, blank=True)
    id_number = models.CharField(db_column='ID_Number', max_length=255, null=True, blank=True)
    email_address = models.CharField(db_column='Email_Address', max_length=255, null=True, blank=True)
    work_dial_code = models.CharField(db_column='Work_Dial_Code', max_length=10, null=True, blank=True)
    work_contact_number = models.CharField(db_column='Work_Contact_Number', max_length=255, null=True, blank=True)
    fax_dial_code = models.CharField(db_column='Fax_Dial_Code', max_length=10, null=True, blank=True)
    fax_number = models.CharField(db_column='Fax_Number', max_length=255, null=True, blank=True)
    mobile_number = models.CharField(db_column='Mobile_Number', max_length=255, null=True, blank=True)
    business_postal_address = models.CharField(db_column='Business_Postal_address', max_length=255, null=True, blank=True)
    post_code = models.CharField(db_column='Post_Code', max_length=10, null=True, blank=True)
    business_physical_address = models.CharField(db_column='Business_Physical_address', max_length=255, null=True, blank=True)
    post_code2 = models.CharField(db_column='Post_Code2', max_length=10, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'cfa3'

class CommunicationsPerson(models.Model):
    member_group_code = models.CharField(db_column='Member_Group_Code', max_length=255, primary_key=True)
    title = models.CharField(db_column='Title', max_length=255, null=True, blank=True)
    first_name = models.CharField(db_column='First_Name', max_length=255, null=True, blank=True)
    surname = models.CharField(db_column='Surname', max_length=255, null=True, blank=True)
    id_number = models.CharField(db_column='ID_Number', max_length=255, null=True, blank=True)
    email_address = models.CharField(db_column='Email_Address', max_length=255, null=True, blank=True)
    work_dial_code = models.CharField(db_column='Work_Dial_Code', max_length=10, null=True, blank=True)
    work_contact_number = models.CharField(db_column='Work_Contact_Number', max_length=255, null=True, blank=True)
    fax_dial_code = models.CharField(db_column='Fax_Dial_Code', max_length=10, null=True, blank=True)
    fax_number = models.CharField(db_column='Fax_Number', max_length=255, null=True, blank=True)
    mobile_number = models.CharField(db_column='Mobile_Number', max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'communications_person'

class HumanResources(models.Model):
    member_group_code = models.CharField(db_column='Member_Group_Code', max_length=255, primary_key=True)
    title = models.CharField(db_column='Title', max_length=255, null=True, blank=True)
    first_name = models.CharField(db_column='First_Name', max_length=255, null=True, blank=True)
    surname = models.CharField(db_column='Surname', max_length=255, null=True, blank=True)
    id_number = models.CharField(db_column='ID_Number', max_length=255, null=True, blank=True)
    email_address = models.CharField(db_column='Email_Address', max_length=255, null=True, blank=True)
    indemnity = models.CharField(db_column='Indemnity', max_length=225, null=True, blank=True)
    work_dial_code = models.CharField(db_column='Work_Dial_Code', max_length=10, null=True, blank=True)
    work_contact_number = models.CharField(db_column='Work_Contact_Number', max_length=255, null=True, blank=True)
    fax_dial_code = models.CharField(db_column='Fax_Dial_Code', max_length=10, null=True, blank=True)
    fax_number = models.CharField(db_column='Fax_Number', max_length=255, null=True, blank=True)
    mobile_number = models.CharField(db_column='Mobile_Number', max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'human_resources'

class Section13a(models.Model):
    member_group_code = models.CharField(db_column='Member_Group_Code', max_length=255, primary_key=True)
    title = models.CharField(db_column='Title', max_length=255, null=True, blank=True)
    first_name = models.CharField(db_column='First_Name', max_length=255, null=True, blank=True)
    surname = models.CharField(db_column='Surname', max_length=255, null=True, blank=True)
    id_number = models.CharField(db_column='ID_Number', max_length=255, null=True, blank=True)
    email_address = models.CharField(db_column='Email_Address', max_length=255, null=True, blank=True)
    indemnity = models.CharField(db_column='Indemnity', max_length=225, null=True, blank=True)
    work_dial_code = models.CharField(db_column='Work_Dial_Code', max_length=10, null=True, blank=True)
    work_contact_number = models.CharField(db_column='Work_Contact_Number', max_length=255, null=True, blank=True)
    fax_dial_code = models.CharField(db_column='Fax_Dial_Code', max_length=10, null=True, blank=True)
    fax_number = models.CharField(db_column='Fax_Number', max_length=255, null=True, blank=True)
    mobile_number = models.CharField(db_column='Mobile_Number', max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'section_13a'

# ==============================================================================
# LOGGING & TRACKING TABLES (UNMANAGED)
# ==============================================================================

class ClientNotes(models.Model):
    notes = models.TextField()
    related_member_group_code = models.CharField(db_column='Member Group Code', max_length=255)
    user = models.CharField(db_column='User', max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    communication_type = models.CharField(max_length=50, null=True, blank=True)
    action_notes = models.CharField(max_length=50, null=True, blank=True)
    attached_email_id = models.CharField(max_length=255, null=True, blank=True)
    attached_file_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'client_notes'
        verbose_name = 'Client Note'
        verbose_name_plural = 'Client Notes'

    def __str__(self):
        return f'Note on {self.related_member_group_code} by {self.user}'

class MemberDocument(models.Model):
    related_member_group_code = models.CharField(max_length=255, verbose_name='Member Group Code')
    document_file = models.FileField(upload_to='pdfs/', verbose_name='Document File')
    title = models.CharField(max_length=255, verbose_name='Document Title', blank=True, null=True)
    uploaded_by = models.CharField(max_length=150, verbose_name='Uploaded By')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    id_document = models.CharField(max_length=45, default='0')
    proof_of_address = models.CharField(max_length=45, default='0')
    bank_statement = models.CharField(max_length=45, default='0')
    appointment_letter = models.CharField(max_length=45, default='0')
    vat_number = models.CharField(max_length=45, default='0')
    mandate_trust_deed = models.CharField(max_length=45, default='0')
    tax_number = models.CharField(max_length=45, default='0')

    class Meta:
        managed = False
        db_table = 'crm_core_memberdocument'

class CrmInbox(models.Model):
    """
    Unmanaged Model: Stores metadata for Outlook emails.
    """
    email_id = models.CharField(max_length=255, primary_key=True) 
    subject = models.CharField(max_length=512, null=True, blank=True)
    sender = models.CharField(max_length=255, null=True, blank=True)
    snippet = models.CharField(max_length=512, null=True, blank=True)
    received_timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending') 
    delegated_by = models.CharField(max_length=100, null=True, blank=True)
    delegated_to = models.CharField(max_length=100, null=True, blank=True)
    
    work_related = models.CharField(max_length=5, default='No')
    # SYNCED: Replaced mip_number with member_group_code pointing to correct db_column
    member_group_code = models.CharField(db_column='Member_Group_Code', max_length=255, null=True, blank=True)
    id_passport = models.CharField(max_length=50, null=True, blank=True)
    category = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=50, null=True, blank=True)
    method = models.CharField(max_length=50, default='Email')
    
    class Meta:
        managed = False
        db_table = 'crm_inbox' 

class CrmDelegateTo(models.Model):
    """
    Unmanaged Model: Full detailed delegation log for Microsoft Graph tasks.
    """
    id = models.AutoField(primary_key=True) 
    email_id = models.CharField(max_length=255, unique=True, db_index=True) 
    subject = models.CharField(max_length=512, null=True, blank=True)
    sender = models.CharField(max_length=255, null=True, blank=True)
    snippet = models.CharField(max_length=512, null=True, blank=True)
    received_timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default='Delegated') 
    delegated_by = models.CharField(max_length=100, null=True, blank=True)
    delegated_to = models.CharField(max_length=100, null=True, blank=True)
    work_related = models.CharField(max_length=5, default='Yes')
    
    # SYNCED: Replaced mip_number with member_group_code pointing to correct db_column
    member_group_code = models.CharField(db_column='Member_Group_Code', max_length=255, null=True, blank=True)
    id_passport = models.CharField(max_length=50, null=True, blank=True)
    category = models.CharField(max_length=50, null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    method = models.CharField(max_length=50, default='Email')
    delegated_attachments = models.TextField(null=True, blank=True) 
    internal_notes = models.TextField(null=True, blank=True)       
    
    class Meta:
        managed = False
        db_table = 'crm_delegate_to'

class CrmDelegateAction(models.Model):
    id = models.AutoField(primary_key=True)
    task_email_id = models.CharField(max_length=255, db_index=True) 
    action_type = models.CharField(max_length=50) 
    action_user = models.CharField(max_length=100)
    action_timestamp = models.DateTimeField(default=timezone.now)
    note_content = models.TextField(null=True, blank=True)
    related_subject = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        managed = False
        db_table = 'crm_delegate_actions'

class DelegationReport(models.Model):
    email_id = models.CharField(primary_key=True, max_length=255)
    subject = models.CharField(max_length=512)
    received_timestamp = models.DateTimeField()
    delegated_by = models.CharField(max_length=100)
    delegated_to = models.CharField(max_length=100)
    DelegationStatus = models.CharField(max_length=20)
    work_related = models.CharField(max_length=5)
    # SYNCED: Replaced mip_number with member_group_code pointing to correct db_column
    member_group_code = models.CharField(db_column='Member_Group_Code', max_length=255)
    EnquiryCategory = models.CharField(max_length=50)
    EnquirySelection = models.CharField(max_length=255)
    TotalActionsTaken = models.IntegerField()
    IsCompleted = models.CharField(max_length=3)
    CompletionTimestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'crm_delegation_report'
        ordering = ['-received_timestamp']

class ComplaintLog(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='complaints_created')
    complainant = models.CharField(max_length=255)
    employer = models.CharField(max_length=255, blank=True, null=True)
    nature_of_complaint = models.TextField()
    resolution = models.TextField(blank=True, null=True)
    created_date = models.DateField(blank=True, null=True)
    resolved_date = models.DateTimeField(blank=True, null=True)
    current_status = models.CharField(max_length=50, default='Open')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'crm_complaint_log'
        ordering = ['-created_at']

class DirectEmail(models.Model):
    email_id = models.AutoField(primary_key=True)
    sender_name = models.CharField(max_length=100, null=True, blank=True) 
    sender_email = models.EmailField(max_length=100) 
    subject = models.CharField(max_length=255, null=True, blank=True) 
    body = models.TextField()
    is_read = models.BooleanField(default=False) 
    received_at = models.DateTimeField(auto_now_add=True) 

    class Meta:
        managed = False 
        db_table = 'direct_emails'
        ordering = ['-received_at']
        
class DirectEmailLog(models.Model):
    member_group_code = models.CharField(max_length=50)
    subject = models.CharField(max_length=255)
    recipient_email = models.CharField(max_length=255)
    body_content = models.TextField()
    sent_by_user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_column='sent_by_user_id')
    sent_at = models.DateTimeField()
    outlook_message_id = models.TextField(null=True, blank=True)
    # New field added below
    action_type = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'crm_direct_email_log'

    def __str__(self):
        return f"{self.subject} to {self.recipient_email}"