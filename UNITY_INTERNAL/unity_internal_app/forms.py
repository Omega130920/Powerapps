from django import forms
from .models import CreditNote, UnityBill, UnityMgListing

class AddMemberForm(forms.ModelForm):
    """
    Form for creating a new UnityMgListing member.
    """
    # Note: Since your model is 'managed = False' (external table), 
    # Django might not auto-create PKs. You must ensure a_company_code is provided.
    
    class Meta:
        model = UnityMgListing
        # Only include the fields you want the user to input
        fields = [
            'a_company_code', 
            'b_company_name', 
            'c_agent', 
            'd_company_status', 
            'e_payment_method',
            'f_billing_method',
            'contact_email',
            # You can add more fields from your model here as needed
        ]
        widgets = {
            'a_company_code': forms.TextInput(attrs={'placeholder': 'Unique Company Code (Required)'}),
            'b_company_name': forms.TextInput(attrs={'placeholder': 'Company Name'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'Contact Email'}),
            # Add custom widgets/placeholders for other fields if desired
        }
        
class PreBillForm(forms.ModelForm):
    """
    Form for manually creating/editing a UnityBill record.
    """
    class Meta:
        model = UnityBill
        fields = [
            'A_CCDatesMonth', 'B_Fund_Code', 'C_Company_Code', 'D_Company_Name', 
            'E_Active_Members', 'F_Pre_Bill_Date', 'G_Schedule_Date', 
            'H_Schedule_Amount', 'I_Submitted_Date', 'J_Final_Date',
            # All deposit fields (K, L, M, N, O, P, Q, R, S, T) are excluded.
        ]
        widgets = {
            'A_CCDatesMonth': forms.DateInput(attrs={'type': 'date'}),
            'F_Pre_Bill_Date': forms.DateInput(attrs={'type': 'date'}),
            'G_Schedule_Date': forms.DateInput(attrs={'type': 'date'}),
            'I_Submitted_Date': forms.DateInput(attrs={'type': 'date'}),
            'J_Final_Date': forms.DateInput(attrs={'type': 'date'}),
            
            'C_Company_Code': forms.HiddenInput(),
            
            'B_Fund_Code': forms.TextInput(),
            'D_Company_Name': forms.TextInput(),
            'E_Active_Members': forms.NumberInput(),
            'H_Schedule_Amount': forms.NumberInput(attrs={'step': '0.01'}),
        }
        labels = {
            'A_CCDatesMonth': 'Bill/Month Date (Required)',
            'B_Fund_Code': 'Fund Code',
            'D_Company_Name': 'Company Name',
            'E_Active_Members': 'Active Members',
            'F_Pre_Bill_Date': 'Pre-Bill Date',
            'G_Schedule_Date': 'Schedule Date',
            'H_Schedule_Amount': 'Scheduled Bill Amount (R)', 
            'I_Submitted_Date': 'Submitted Date',
            'J_Final_Date': 'Final Date',
        }
        
class FiscalDateAssignmentForm(forms.ModelForm):
    target_bill_id = forms.ModelChoiceField(
        queryset=UnityBill.objects.none(), 
        label="Assign Credit to Bill:",
        required=False,
        empty_label="--------- Do Not Assign to Bill ---------",
        help_text="Optional: Select a Bill to assign this entire credit line against. This will link the credit to the bill's offset calculation."
    )
    
    class Meta:
        model = CreditNote
        fields = ['fiscal_date', 'review_note']
        widgets = {
            'fiscal_date': forms.DateInput(attrs={'type': 'date', 'required': True}),
            'review_note': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Add notes regarding this credit line assignment.'}),
        }

    def __init__(self, *args, company_code=None, context_type='summary', **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Setup target_bill_id queryset
        if company_code:
            queryset = UnityBill.objects.filter(
                C_Company_Code=company_code
            ).order_by('-A_CCDatesMonth')
            self.fields['target_bill_id'].queryset = queryset
            self.fields['target_bill_id'].label_from_instance = lambda obj: f"Bill {obj.id}: {obj.A_CCDatesMonth.strftime('%Y-%m-%d')} (R{obj.H_Schedule_Amount:.2f})"
        
        # 2. Control visibility based on context_type (CRITICAL FIX)
        
        if context_type == 'info':
            # CONTEXT: unity_information tab -> Only Fiscal Date is required/visible
            self.fields['target_bill_id'].widget = forms.HiddenInput()
            self.fields['target_bill_id'].required = False
            self.fields['fiscal_date'].required = True 
            self.fields['review_note'].required = False

        elif context_type == 'summary':
            # CONTEXT: pre_bill_summary page -> Both Bill Assignment and Fiscal Date should be visible/submittable
            # We enforce fiscal_date is required to allow auto-allocation lookup.
            # self.fields['fiscal_date'].widget = forms.HiddenInput() # <-- REMOVED THIS CONFLICTING LINE
            self.fields['fiscal_date'].required = True # Now required in summary too
            self.fields['review_note'].required = False
        
        # 3. Set initial data for target_bill_id 
        initial_bill = self.instance.assigned_unity_bill if self.instance else None
        if initial_bill and initial_bill in self.fields['target_bill_id'].queryset:
            self.fields['target_bill_id'].initial = initial_bill
            
from .models import UnityClaim

class UnityClaimForm(forms.ModelForm):
    class Meta:
        model = UnityClaim
        # Using __all__ will now pick up 'mip_number' and 'claim_amount' from the model
        fields = '__all__'
        
        widgets = {
            # --- Personal & Identification ---
            'id_number': forms.TextInput(attrs={'class': 'form-input'}),
            'member_name': forms.TextInput(attrs={'class': 'form-input'}),
            'member_surname': forms.TextInput(attrs={'class': 'form-input'}),
            'mip_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter MIP Number'}),
            
            # --- Dropdowns ---
            'claim_type': forms.Select(attrs={'class': 'form-select', 'id': 'claim_type_select'}),
            'exit_reason': forms.Select(attrs={'class': 'form-select'}),
            'claim_allocation': forms.Select(attrs={'class': 'form-select'}),
            'claim_status': forms.Select(attrs={'class': 'form-select', 'id': 'claim_status_select'}),
            'payment_option': forms.Select(attrs={'class': 'form-select', 'id': 'payment_option_select'}),
            
            # --- Currency/Numbers ---
            'claim_amount': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '0.00'}),

            # --- Dates ---
            'claim_created_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'last_contribution_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'date_submitted': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'date_paid': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            
            # --- System/Readonly Fields ---
            'company_code': forms.TextInput(attrs={'class': 'form-input', 'readonly': 'readonly'}),
            'agent': forms.TextInput(attrs={'class': 'form-input', 'readonly': 'readonly'}),
            'linked_email_id': forms.HiddenInput(), # Usually handled manually in the view via logic
        }

    def __init__(self, *args, **kwargs):
        super(UnityClaimForm, self).__init__(*args, **kwargs)
        # Ensure fields that are not compulsory in your Two Pot logic are not required by the form
        self.fields['mip_number'].required = False
        self.fields['claim_amount'].required = False
        self.fields['exit_reason'].required = False
        self.fields['last_contribution_date'].required = False
        self.fields['date_paid'].required = False