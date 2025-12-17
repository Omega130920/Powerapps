from django import forms
from .models import LevyData, TsrfPdfDocument # <-- IMPORT the new TsrfPdfDocument model

class AddLevyForm(forms.ModelForm):
    """
    Form for creating a new LevyData record.
    We are excluding many fields to keep the manual entry simple and focused.
    """
    
    # Customise the date input widgets for better UX
    commencement_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
        required=False
    )
    termination_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
        required=False
    )
    
    class Meta:
        model = LevyData
        # Include core fields and initial contact fields
        fields = [
            'levy_number', 
            'levy_name', 
            'mip_status', 
            'commencement_date', 
            'termination_date', 
            'responsible_person', 
            'registration_number', 
            'notice_email',
            'telephone',
            'postal_address',
            'physical_address',
        ]
        widgets = {
            'levy_number': forms.TextInput(attrs={'placeholder': 'Unique Levy Number (Required)'}),
            'levy_name': forms.TextInput(attrs={'placeholder': 'Full Company/Trust Name'}),
            'notice_email': forms.EmailInput(attrs={'placeholder': 'Contact Email'}),
        }

# =========================================================================
# NEW FORM FOR PDF UPLOADS
# =========================================================================

class DocumentUploadForm(forms.ModelForm):
    """
    Form for uploading FICA documents to the TsrfPdfDocument table.
    We only expose 'title' and 'document_file' for user input.
    Other fields (levy_number, uploaded_by, uploaded_at, FICA tracking) 
    are set dynamically in views.py.
    """
    # The 'title' field will hold the Fica_X code from the HTML select.
    # The 'document_file' field will handle the PDF upload.
    
    class Meta:
        model = TsrfPdfDocument
        # Only expose the two fields that the user selects/uploads
        fields = ['title', 'document_file']
        widgets = {
            # Use FileInput and restrict to PDF MIME type for client-side filtering
            'document_file': forms.FileInput(attrs={'accept': 'application/pdf'}),
            
            # The title is set by a custom <select> in the template, 
            # so we render it as a HiddenInput here to let the template handle the UI.
            'title': forms.HiddenInput(), 
        }