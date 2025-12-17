# TSRF_RECON_APP/models.py

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

# Get the User model dynamically
# Note: This requires 'django.contrib.auth' to be in INSTALLED_APPS
User = get_user_model() 

# =========================================================================
# EXISTING UNMANAGED MODELS (Data Tables)
# =========================================================================

class LevyData(models.Model):
    """
    Model representing the 'levy data' table.
    """
    levy_number = models.CharField(db_column='Levy_Number', max_length=255, primary_key=True)
    levy_name = models.CharField(db_column='Levy_Name', max_length=255, blank=True, null=True)
    mip_status = models.CharField(db_column='MIP_Status', max_length=255, blank=True, null=True)
    commencement_date = models.DateField(db_column='Commencement_Date', blank=True, null=True)
    termination_date = models.DateField(db_column='Termination_Date', blank=True, null=True)
    responsible_person = models.CharField(db_column='Responsible_Person', max_length=255, blank=True, null=True)
    registration_number = models.CharField(db_column='Registration_Number', max_length=255, blank=True, null=True)
    fica = models.CharField(db_column='FICA', max_length=255, blank=True, null=True)
    levy_user = models.CharField(db_column='Levy_User', max_length=255, blank=True, null=True)
    user_login = models.CharField(db_column='User_Login', max_length=255, blank=True, null=True)
    levy_user_2 = models.CharField(db_column='Levy_User_2', max_length=255, blank=True, null=True)
    user_login_2 = models.CharField(db_column='User_Login_2', max_length=255, blank=True, null=True)
    notice_email = models.CharField(db_column='Notice_Email', max_length=255, blank=True, null=True)
    telephone = models.CharField(db_column='Telephone', max_length=255, blank=True, null=True)
    postal_address = models.CharField(db_column='Postal_Address', max_length=255, blank=True, null=True)
    physical_address = models.CharField(db_column='Physical_Address', max_length=255, blank=True, null=True)
    director_name_1 = models.CharField(db_column='Director_Name_1', max_length=255, blank=True, null=True)
    director_mail_1 = models.CharField(db_column='Director_Mail_1', max_length=255, blank=True, null=True)
    director_cell_1 = models.CharField(db_column='Director_Cell_1', max_length=255, blank=True, null=True)
    director_address_1 = models.CharField(db_column='Director_Address_1', max_length=255, blank=True, null=True)
    director_name_2 = models.CharField(db_column='Director_Name_2', max_length=255, blank=True, null=True)
    director_mail_2 = models.CharField(db_column='Director_Mail_2', max_length=255, blank=True, null=True)
    director_cell_2 = models.CharField(db_column='Director_Cell_2', max_length=255, blank=True, null=True)
    director_address_2 = models.CharField(db_column='Director_Address_2', max_length=255, blank=True, null=True)
    director_name_3 = models.CharField(db_column='Director_Name_3', max_length=255, blank=True, null=True)
    director_mail_3 = models.CharField(db_column='Director_Mail_3', max_length=255, blank=True, null=True)
    director_cell_3 = models.CharField(db_column='Director_Cell_3', max_length=255, blank=True, null=True)
    director_address_3 = models.CharField(db_column='Director_Address_3', max_length=255, blank=True, null=True)
    director_name_4 = models.CharField(db_column='Director_Name_4', max_length=255, blank=True, null=True)
    director_mail_4 = models.CharField(db_column='Director_Mail_4', max_length=255, blank=True, null=True)
    director_cell_4 = models.CharField(db_column='Director_Cell_4', max_length=255, blank=True, null=True)
    director_address_4 = models.CharField(db_column='Director_Address_4', max_length=255, blank=True, null=True)
    administrator = models.CharField(db_column='Administrator', max_length=255, blank=True, null=True)
    termination_reason = models.CharField(db_column='Termination_Reason', max_length=255, blank=True, null=True)
    termination_status = models.CharField(db_column='Termination_Status', max_length=255, blank=True, null=True)
    attorney_case = models.CharField(db_column='Attorney_Case', max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'levy data'

class AllEmployerStaticData(models.Model):
    Levy_Number = models.CharField(max_length=255, unique=True, primary_key=True)
    Registered_Company_Name = models.CharField(max_length=255, null=True, blank=True)
    CC_number_Trust_number_ID_Number = models.CharField(max_length=255, null=True, blank=True)
    Contact_Number_1 = models.CharField(max_length=255, null=True, blank=True)
    Contact_Number_2 = models.CharField(max_length=255, null=True, blank=True)
    Mobile_Number = models.CharField(max_length=255, null=True, blank=True)
    Physical_Street_Address = models.CharField(max_length=255, null=True, blank=True)
    Postal_Street_Address = models.CharField(max_length=255, null=True, blank=True)
    Delivery_Instructions = models.CharField(max_length=255, null=True, blank=True)
    Director_1_Full_Name_Surname = models.CharField(max_length=255, null=True, blank=True)
    Director_1_ID_Number = models.CharField(max_length=255, null=True, blank=True)
    Director_1_Email_Address = models.CharField(max_length=255, null=True, blank=True)
    Director_1_Cell_Number = models.CharField(max_length=255, null=True, blank=True)
    Director_1_Address = models.CharField(max_length=255, null=True, blank=True)
    Director_2_Full_Name_Surname = models.CharField(max_length=255, null=True, blank=True)
    Director_2_ID_Number = models.CharField(max_length=255, null=True, blank=True)
    Director_2_Email_Address = models.CharField(max_length=255, null=True, blank=True)
    Director_2_Cell_Number = models.CharField(max_length=255, null=True, blank=True)
    Director_2_Address = models.CharField(max_length=255, null=True, blank=True)
    Director_3_Full_Name_Surname = models.CharField(max_length=255, null=True, blank=True)
    Director_3_ID_Number = models.CharField(max_length=255, null=True, blank=True)
    Director_3_Email_Address = models.CharField(max_length=255, null=True, blank=True)
    Director_3_Cell_Number = models.CharField(max_length=255, null=True, blank=True)
    Director_3_Address = models.CharField(max_length=255, null=True, blank=True)
    Director_4_Full_Name_Surname = models.CharField(max_length=255, null=True, blank=True)
    Director_4_ID_Number = models.CharField(max_length=255, null=True, blank=True)
    Director_4_Email_Address = models.CharField(max_length=255, null=True, blank=True)
    Director_4_Cell_Number = models.CharField(max_length=255, null=True, blank=True)
    Director_4_Address = models.CharField(max_length=255, null=True, blank=True)
    Responsible_Person_Full_Name_Surname = models.CharField(max_length=255, null=True, blank=True)
    Responsible_Person_ID_Number = models.CharField(max_length=255, null=True, blank=True)
    Responsible_Person_Email_Address = models.CharField(max_length=255, null=True, blank=True)
    Responsible_Person_Cell_Number = models.CharField(max_length=255, null=True, blank=True)
    Responsible_Person_Address = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'all employer static data'

class ClientNotes(models.Model):
    """
    Model representing notes associated with a levy,
    mapped to the 'client_notes' table.
    """
    # NOTE: Django will use an auto-ID field if you don't define a PK, which is fine here.
    levy_number = models.CharField(db_column='Levy_number', max_length=255)
    notes_text = models.TextField(db_column='notes')
    user = models.CharField(db_column='User', max_length=255)
    date = models.DateTimeField(db_column='date', auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'client_notes'
        verbose_name = 'Client Note'
        verbose_name_plural = 'Client Notes'

    def __str__(self):
        return f'Note on {self.levy_number} by {self.user}'
    
class LevyDataDirectors(models.Model):
    """
    A model to represent the levy_data_directors table.
    """
    # NOTE: Django requires a primary key, so we rely on the implicit auto-ID unless 
    # the MySQL table has a primary key column not named 'id'.
    Director_Name_1 = models.CharField(max_length=255, null=True, blank=True)
    Director_Mail_1 = models.CharField(max_length=255, null=True, blank=True)
    Director_Cell_1 = models.CharField(max_length=255, null=True, blank=True)
    Director_Address_1 = models.CharField(max_length=255, null=True, blank=True)

    Director_Name_2 = models.CharField(max_length=255, null=True, blank=True)
    Director_Mail_2 = models.CharField(max_length=255, null=True, blank=True)
    Director_Cell_2 = models.CharField(max_length=255, null=True, blank=True)
    Director_Address_2 = models.CharField(max_length=255, null=True, blank=True)

    Director_Name_3 = models.CharField(max_length=255, null=True, blank=True)
    Director_Mail_3 = models.CharField(max_length=255, null=True, blank=True)
    Director_Cell_3 = models.CharField(max_length=255, null=True, blank=True)
    Director_Address_3 = models.CharField(max_length=255, null=True, blank=True)

    Director_Name_4 = models.CharField(max_length=255, null=True, blank=True)
    Director_Mail_4 = models.CharField(max_length=255, null=True, blank=True)
    Director_Cell_4 = models.CharField(max_length=255, null=True, blank=True)
    Director_Address_4 = models.CharField(max_length=255, null=True, blank=True)

    Levy_Number = models.CharField(max_length=225, unique=True, help_text="The unique levy number.")

    def __str__(self):
        return f"Levy Number: {self.Levy_Number}"
    
    class Meta:
        managed = False
        db_table = 'levy_data_directors'
        verbose_name = 'Levy Director'
        verbose_name_plural = 'Levy Directors'
        
class BankLine(models.Model):
    
    id = models.BigAutoField(primary_key=True)
    """
    Model representing a single line item from the bank statement,
    corresponding to the 'bank_line' MySQL table.
    """
    Date = models.DateField(
        help_text="The date of the transaction."
    )
    Amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="The monetary amount of the transaction."
    )
    Reference_Description = models.CharField(
        max_length=255, 
        help_text="Primary reference or description."
    )
    Other_Reference = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Secondary reference."
    )
    Recon = models.CharField(
        max_length=255,
        blank=True, 
        null=True,
        help_text="Reconciliation status or flag."
    )
    Levy_number = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Levy information."
    )
    Fisical = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Fiscal period or information."
    )
    Type = models.CharField(
        max_length=255, 
        help_text="Transaction type (e.g., DEBIT, CREDIT)."
    )
    Import_date = models.DateField(
        auto_now_add=True, # Automatically set the date when the record is created
        help_text="The date the record was imported into the database."
    )
    Column_5 = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Placeholder column 5 from the CSV."
    )
    Column_6 = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Placeholder column 6 from the CSV."
    )

    class Meta:
        db_table = 'bank_line' 
        managed = False # Explicitly set for existing table

    def __str__(self):
        return f"{self.Date} - {self.Amount} - {self.Reference_Description}"
    
class Org(models.Model):
    """
    Model representing the ORG Reconciliation Data.
    """
    id = models.BigAutoField(primary_key=True) 
    
    levy_number = models.CharField(max_length=255, verbose_name="Levy Number", db_column='Levy_Number')
    
    employer_name = models.CharField(max_length=255, verbose_name="Employer Name")
    billing_period = models.CharField(max_length=255, verbose_name="Billing Period")
    cbr_status = models.CharField(max_length=255, verbose_name="CBR Status", null=True, blank=True)

    member_arrear_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Member Arrear Total")
    member_additional_voluntary_contribution_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Member Add. Voluntary Contrib. Total")
    member_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Member Total")
    employer_arrear_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Employer Arrear Total")
    employer_additional_voluntary_contribution_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Employer Add. Voluntary Contrib. Total")
    employer_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Employer Total")
    due_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Due Amount")
    overs_unders = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Overs/Unders")

    import_date = models.DateField(verbose_name="Import Date") 
    created_at = models.DateTimeField(verbose_name="Created At", null=True, blank=True)

    class Meta:
        db_table = 'org'
        managed = False 
        verbose_name = "ORG Record"
        verbose_name_plural = "ORG Records"
        
    def __str__(self):
        return f"{self.levy_number} - {self.billing_period}"
    
class TsrfPdfDocument(models.Model):
    related_levy_number = models.CharField(max_length=255, verbose_name="Levy Number") 
    document_file = models.FileField(upload_to='levy_docs/', verbose_name="Document File") 
    title = models.CharField(max_length=255, verbose_name="Document Type") 
    uploaded_by = models.CharField(max_length=150, verbose_name="Uploaded By") 
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Uploaded At") 
    
    id_document = models.CharField(max_length=45, default='0', verbose_name="ID Document")
    proof_of_address = models.CharField(max_length=45, default='0', verbose_name="Proof of Address")
    bank_statement = models.CharField(max_length=45, default='0', verbose_name="Bank Statement")
    appointment_letter = models.CharField(max_length=45, default='0', verbose_name="Appointment Letter")
    vat_number = models.CharField(max_length=45, default='0', verbose_name="VAT Number")
    mandate_trust_deed = models.CharField(max_length=45, default='0', verbose_name="Mandate/Trust Deed")
    tax_number = models.CharField(max_length=45, default='0', verbose_name="Tax Number")

    class Meta:
        managed = False 
        db_table = 'tsrf_pdfdocument'

    def __str__(self):
        return f"{self.related_levy_number} - {self.title}"

class OrgNotes(models.Model):
    """
    Model for the existing 'org_notes' table in MySQL.
    """
    ID = models.IntegerField(primary_key=True, db_column='ID') 
    
    Levy_number = models.TextField(db_column='Levy_number', verbose_name="Levy Number")
    Date = models.DateTimeField(db_column='date', verbose_name="Note Date")
    User = models.TextField(db_column='User', verbose_name="User")
    Fiscal_date = models.DateField(db_column='fiscal_date', null=True, blank=True, verbose_name="Fiscal Period Date")
    Notes = models.TextField(db_column='notes', verbose_name="Note Text")

    class Meta:
        db_table = 'org_notes' 
        managed = False 
        verbose_name = "ORG Note (Unmanaged)"
        verbose_name_plural = "ORG Notes (Unmanaged)"

    def __str__(self):
        return f"Note ID {self.ID} for Levy {self.Levy_number}"

# =========================================================================
# NEW MANAGED MODELS (Delegation/Task System)
# These will create the tables when you run 'makemigrations' and 'migrate'.
# =========================================================================

# --- CHOICES FOR DELEGATION MODELS ---
STATUS_CHOICES = (
    ('NEW', 'New'),
    ('DEL', 'Delegated'),
    ('PRG', 'In Progress'),
    ('ACT', 'Actioned'),
    ('COM', 'Completed'),
    ('DLT', 'Recycle_bin'), # Added DLT status
)

CATEGORY_CHOICES = (
    ('Schedule', 'Schedule'),
    ('Claim', 'Claim'),
    ('Query', 'Query'),
    ('Bank', 'Bank'),
)

# =========================================================================
# EXISTING UNMANAGED MODELS (Data Tables) - (Omitting previous definitions 
# for brevity, but they remain unchanged and set to managed=False)
# =========================================================================

# class LevyData(models.Model): ... managed = False
# class AllEmployerStaticData(models.Model): ... managed = False
# class ClientNotes(models.Model): ... managed = False
# class LevyDataDirectors(models.Model): ... managed = False
# class BankLine(models.Model): ... managed = False
# class Org(models.Model): ... managed = False
# class TsrfPdfDocument(models.Model): ... managed = False
# class OrgNotes(models.Model): ... managed = False


# =========================================================================
# NEW UNMANAGED DELEGATION MODELS (Task System)
# Set to managed=False because you created the tables manually via SQL.
# =========================================================================

# =========================================================================
# NEW UNMANAGED DELEGATION MODELS (Task System)
# =========================================================================

class EmailDelegation(models.Model):
    """Represents an email assigned to an agent for action."""
    # Django uses 'id' by default; matches your 'bigint AI PK'
    email_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='NEW')
    work_related = models.BooleanField(default=True)
    received_at = models.DateTimeField(null=True, blank=True)
    
    # ForeignKey mapping to your SQL 'assigned_user_id' column
    assigned_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        db_column='assigned_user_id', # Matches your SQL column
        related_name='tsrf_delegated_emails'
    )
    
    company_code = models.CharField(max_length=100, null=True, blank=True)
    email_category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, null=True, blank=True)

    class Meta:
        managed = False 
        db_table = 'tsrf_email_delegation'
        verbose_name = 'TSRF Email Delegation'
        verbose_name_plural = 'TSRF Email Delegations'

class DelegationNote(models.Model):
    """Stores internal notes for a specific delegation task."""
    delegation = models.ForeignKey(
        EmailDelegation, 
        on_delete=models.CASCADE, 
        db_column='delegation_id', # Matches your SQL column
        related_name='notes'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        db_column='user_id' # Matches your SQL column
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    action_type = models.CharField(max_length=50, default='Note')

    class Meta:
        managed = False
        db_table = 'tsrf_delegation_note'
        ordering = ['-created_at']

class EmailTransaction(models.Model):
    """Logs external communication (replies sent) against a task."""
    delegation = models.ForeignKey(
        EmailDelegation, 
        on_delete=models.CASCADE, 
        db_column='delegation_id', # Matches your SQL column
        related_name='transactions'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        db_column='user_id' # Matches your SQL column
    )
    subject = models.CharField(max_length=255)
    recipient = models.EmailField(max_length=254)
    sent_at = models.DateTimeField(auto_now_add=True)
    action_type = models.CharField(max_length=50, default='Reply Sent')

    class Meta:
        managed = False
        db_table = 'tsrf_email_transaction'

class TSRFReconOutlookToken(models.Model):
    """Stores Microsoft Graph access tokens."""
    # Your SQL uses 'id' as AI PK and 'user_id' as the FK
    id = models.AutoField(primary_key=True) 
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        db_column='user_id', # Matches your SQL column
        unique=True
    )
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'tsrf_recon_outlooktoken'