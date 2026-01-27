from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # Core authentication and dashboard
    path('', views.login_view, name='root'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),

    # Unity Listing and Info
    path('unity-data/', views.unity_list, name='unity_list'),
    path('unity-data/<str:company_code>/', views.unity_information, name='unity_information'),
    path('add-member/', views.add_member_view, name='add_member'),

    # Bank Reconciliation
    path('import-data/', views.import_excel_view, name='import_data'),
    path('bank-list/', views.bank_list, name='bank_list'),
    path('bankline-recon/<int:record_id>/', views.bankline_recon, name='bankline_recon'),
    path('recon/pdf/<int:recon_id>/', views.generate_recon_statement, name='generate_recon_statement'),

    # Bankline Review
    path('bankline/review/<int:recon_id>/', views.display_bankline_review, name='display_bankline_review'),
    path('bankline/review/update/<int:recon_id>/', views.update_bankline_details, name='update_bankline_details'),

    # Billing & Settlement
    path('unity-billing/create/<str:company_code>/', views.create_pre_bill, name='create_pre_bill'),
    path('unity-billing/<str:company_code>/', views.unity_billing_history, name='unity_billing_history'),

    # Edit Bill
    path('unity-billing/edit/<str:company_code>/<int:bill_id>/',
        views.edit_bill,
        name='edit_bill'),

    # Bill Summary View
    path('pre-bill/summary/<str:company_code>/<int:bill_id>/',
        views.pre_bill_reconciliation_summary, name='pre_bill_reconciliation_summary'),

    # Cash Allocation
    path('pre-bill/process-cash/<str:company_code>/<int:bill_id>/',
        views.process_cash_allocation,
        name='process_cash_allocation'),

    # Bill Finalization
    path('unity/reconcile-bill/<str:company_code>/<int:bill_id>/',
        views.finalize_reconciliation,
        name='finalize_reconciliation'),

    # Process Bill Settlement (Likely Redundant)
    path('pre-bill/process/<str:company_code>/<int:bill_id>/',
        views.process_bill_settlement, name='process_bill_settlement'),

    # Credit Note Import
    path('import-credit/', views.import_credit, name='import_credit'),

    # Credit Note / Imported Data Processing
    path('credit-note/list/', views.credit_note_list, name='credit_note_list'),
    path('credit-note/assign/<int:note_id>/', views.assign_fiscal_date_view, name='assign_fiscal_date'),
    path('credit-note/assign/<int:note_id>/<str:context_type>/', views.assign_fiscal_date_view, name='assign_fiscal_date_context'),
    path('allocate-surplus/<int:bill_id>/', views.allocate_surplus_to_bill, name='allocate_surplus_to_bill'),
    path('report/settle-bill/<str:company_code>/<int:bill_id>/', views.settle_bill_report, name='settle_bill_report'),
    path('export/settled-bill/<str:company_code>/<int:bill_id>/', views.export_settled_bill_csv, name='export_settled_bill_csv'),

    # Global History Export/Overview
    path('export/global-history/', views.global_history_overview, name='export_global_bill_history'),
    path('export/global-history/download/', views.export_global_history_csv, name='export_global_history_csv'),

    # Claims
    path('save-claim/<str:company_code>/', views.save_claim, name='save_claim'),
    path('global-claims/', views.global_claims_view, name='global_claims'),

    # Global Claims
    path('save-claim-global/', views.save_global_claim, name='save_global_claim'),
    path('claims/two-pot/', views.global_two_pot_view, name='global_two_pot'),

    path('unallocate-surplus/<int:bill_id>/', views.unallocate_surplus, name='unallocate_surplus_from_bill'),
    path('admin-billing/', views.admin_billing_view, name='admin_billing'),
    path('confirmations/', views.confirmations_view, name='confirmations'),
    
        # --- Outlook DELEGATOR Paths (Inbox & Assignment) ---
    path('outlook/', views.outlook_dashboard_view, name='outlook_dashboard'), 
    path('outlook/send/', views.send_email_view, name='send_email'), 
    
    # --- Outlook DELEGATED Paths (Assigned User Workflow) ---
    path('outlook/delegated/', views.outlook_delegated_box, name='outlook_delegated_box'),
    path('outlook/delegated/<int:delegation_id>/action/', 
         views.outlook_delegated_action, 
         name='outlook_delegated_action'),
    path('outlook/delegate/<str:email_id>/', views.outlook_delegate_to, name='outlook_delegate_to'),
    path('outlook/recycle-bin/', views.outlook_recycle_bin_view, name='outlook_recycle_bin'),
    path('outlook/action/<int:delegation_id>/', views.outlook_delegated_action, name='outlook_delegated_action'),
    path('outlook/delete-permanent/', views.outlook_delete_permanent, name='outlook_delete_permanent'),
    path('view-email-thread/<str:email_id>/', views.view_email_thread, name='view_email_thread'),
    path('emails/archive/', views.email_list_view, name='email_list'),
    
    path('export_two_pot_excel/', views.export_two_pot_excel, name='export_two_pot_excel'),
    path('export_global_claims_excel/', views.export_global_claims_excel, name='export_global_claims_excel'),
    path('manager/credit-approvals/', views.manager_approval_dashboard, name='manager_approval_dashboard'),
    path('manager/approve-link/<int:note_id>/', views.approve_credit_link, name='approve_credit_link'),
    path('manager/reject-link/<int:note_id>/', views.reject_credit_link, name='reject_credit_link'),
    path('bank/global/', views.global_bank_view, name='global_bank'),
    path('bank/global/export/', views.export_global_bank_excel, name='export_global_bank_excel'),
    path('outlook/download/<str:message_id>/<str:attachment_id>/', views.download_attachment_view, name='download_attachment'),
    
    path('emails/archive/', views.email_list_view, name='email_list'), # The HTML view
    path('emails/export/', views.export_email_list, name='export_email_list'),
    path('download-email/<str:email_id>/', views.download_email_file, name='download_email_file'),
]