# crm_core/forms.py
from django import forms
from .models import (
    ComplaintLog, MemberDocument, GlobalFundContact, Cbc, CbcAdminPerson, CbcConsultancyPerson,
    Cfa, CfaAdminPerson, Cfa2, Cfa3, CommunicationsPerson, 
    HumanResources, Section13a, MedicalCorrespondence  # 🟢 Added MedicalCorrespondence here
)

# =================================================================
# 1. Existing Form (Document Upload)
# =================================================================
class DocumentUploadForm(forms.ModelForm):
    # Set the accept attribute to only allow PDF files in the browser dialog
    document_file = forms.FileField(
        label='Select PDF File',
        widget=forms.FileInput(attrs={'accept': '.pdf'})
    )
    
    class Meta:
        model = MemberDocument
        # Note: 'title' is used here, which you previously identified as document_type
        fields = ['title', 'document_file']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Optional: Enter a document title or description'}),
        }

# =================================================================
# 2. New Member Creation Forms
# =================================================================

# --- Primary Form (Captures the new Member_Group_Code, which is the PK) ---
class GlobalFundContactForm(forms.ModelForm):
    class Meta:
        model = GlobalFundContact
        fields = [
            'member_group_code', 'member_group_name', 'commencement_date', 
            'fund_status', 'business_postal_address', 'business_postal_address_post_code', 
            'business_physical_address2', 'business_physical_address_post_code2'
        ]
        labels = {
            'member_group_code': 'Member Group Code (Required)',
            'member_group_name': 'Member Group Name (Required)',
        }

# --- Related Forms (Exclude member_group_code, as the view sets it after GlobalFundContact saves) ---

class CbcForm(forms.ModelForm):
    class Meta:
        model = Cbc
        exclude = ('member_group_code',)

class CbcAdminPersonForm(forms.ModelForm):
    class Meta:
        model = CbcAdminPerson
        exclude = ('member_group_code',)

class CbcConsultancyPersonForm(forms.ModelForm):
    class Meta:
        model = CbcConsultancyPerson
        exclude = ('member_group_code',)

class CfaForm(forms.ModelForm):
    class Meta:
        model = Cfa
        exclude = ('member_group_code',)

class CfaAdminPersonForm(forms.ModelForm):
    class Meta:
        model = CfaAdminPerson
        exclude = ('member_group_code',)

class Cfa2Form(forms.ModelForm):
    class Meta:
        model = Cfa2
        exclude = ('member_group_code',)

class Cfa3Form(forms.ModelForm):
    class Meta:
        model = Cfa3
        exclude = ('member_group_code',)

class CommunicationsPersonForm(forms.ModelForm):
    class Meta:
        model = CommunicationsPerson
        exclude = ('member_group_code',)

class HumanResourcesForm(forms.ModelForm):
    class Meta:
        model = HumanResources
        exclude = ('member_group_code',)

class Section13aForm(forms.ModelForm):
    class Meta:
        model = Section13a
        exclude = ('member_group_code',)

# --- New Medical Correspondence Form ---
class MedicalCorrespondenceForm(forms.ModelForm):
    class Meta:
        model = MedicalCorrespondence
        exclude = ('member_group_code',)
        
# =================================================================
# 3. NEW: Complaint Log Form
# =================================================================

# =================================================================
# 3. NEW: Complaint Log Form
# =================================================================

class ComplaintLogForm(forms.ModelForm):
    class Meta:
        model = ComplaintLog
        # Fields updated to include requirements 12.1 and 12.3
        fields = [
            'complainant', 
            'employer', 
            'member_number',       # New: 12.1
            'id_passport_number',  # New: 12.1
            'pfa',                 # New: 12.1 (Dropdown)
            'nature_of_complaint', 
            'action_taken',        # New: 12.3 (Free-text)
            'resolution', 
            'created_date', 
            'resolved_date', 
            'current_status'       # Updated choices in model will reflect here
        ]
        
        widgets = {
            'nature_of_complaint': forms.Textarea(attrs={'rows': 3, 'class': 'w-full p-2 border rounded'}),
            'action_taken': forms.Textarea(attrs={'rows': 3, 'class': 'w-full p-2 border rounded'}), # New widget
            'resolution': forms.Textarea(attrs={'rows': 3, 'class': 'w-full p-2 border rounded'}),
            
            # Date/DateTime widgets
            'created_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-2 border rounded'}),
            'resolved_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full p-2 border rounded'}),
            
            # Standard Text Inputs
            'complainant': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'employer': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'member_number': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),      # New widget
            'id_passport_number': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}), # New widget
            
            # Select/Dropdowns
            'pfa': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),            # New widget
            'current_status': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
        }