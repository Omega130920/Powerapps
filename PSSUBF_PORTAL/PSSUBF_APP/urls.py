from django.urls import path
from . import views

urlpatterns = [
    # 1. The Main Menu / Switchboard (Renders dashboard.html)
    path('', views.pssubf_switchboard, name='pssubf_switchboard'),
    
    # 2. Live Inbox List (Renders inbox_list.html from pssubf_inbox table)
    path('inbox/', views.outlook_dashboard_view, name='pssubf_dashboard'),
    
    # 3. Active Delegations List (Renders delegations_list.html from pssubf_delegate table)
    path('delegations/', views.pssubf_delegations_list, name='pssubf_delegations_list'),
    
    # 4. Audit Logs / Action History (Renders audit_logs.html from pssubf_actions table)
    path('audit-logs/', views.pssubf_audit_logs, name='pssubf_audit_logs'),
    
    # --- Task Specific Logic ---
    
    # View to perform the delegation
    path('delegate/<str:email_id>/', views.pssubf_delegate_view, name='pssubf_delegate'),
    
    # Detail view for an assigned task
    path('action/<str:email_id>/', views.pssubf_action_view, name='pssubf_action'),
    
    # View full email thread and action history
    path('thread/<str:email_id>/', views.pssubf_view_thread, name='pssubf_thread'),
    
    # Download route for Graph API attachments
    path('download/<str:message_id>/<str:attachment_id>/', views.download_pssubf_attachment, name='download_pssubf_attachment'),
    path('sync/', views.sync_pssubf_inbox, name='sync_inbox'),
    path('recycle-bin/', views.pssubf_recycle_bin, name='pssubf_recycle_bin'),
    path('restore/<str:email_id>/', views.pssubf_restore_item, name='pssubf_restore'),
    path('recycle-view/<str:email_id>/', views.pssubf_recycle_view, name='pssubf_recycle_view'),
    path('delete-permanent/<str:email_id>/', views.pssubf_delete_permanent, name='pssubf_delete_permanent'),
    path('bulk-delete/', views.pssubf_bulk_delete, name='pssubf_bulk_delete'),
    path('history-preview/<str:email_id>/', views.pssubf_history_preview, name='pssubf_history_preview'),
    path('pssubf/beneficiaries/import/', views.beneficiary_import_view, name='beneficiary_import'),
    path('pssubf/beneficiaries/list/', views.beneficiary_list_view, name='beneficiary_list'),
    path('beneficiaries/export/', views.export_beneficiaries_excel, name='export_beneficiaries'),
    path('pssubf/beneficiaries/details/<str:membership_number>/', views.beneficiary_details_view, name='beneficiary_details'),
    path('claims/', views.claim_list_view, name='claim_list'),
    path('adhoc/', views.ad_hoc_list_view, name='adhoc_list'),
    path('get-beneficiary-data/<str:membership_number>/', views.get_beneficiary_data, name='get_beneficiary_data'),
    path('get-claim-details/<int:claim_id>/', views.get_claim_details, name='get_claim_details'),
    
    # NEW PATH ADDED FOR AD HOC MODAL DATA FETCHING
    path('get-adhoc-details/<int:record_id>/', views.get_adhoc_details, name='get_adhoc_details'),
    
    path('export-adhoc/', views.export_adhoc_excel, name='export_adhoc'),
    path('claims/export/', views.export_claims_excel, name='export_claims'),
    path('affordability-tool/', views.affordability_dashboard, name='affordability_dashboard'),
    path('affordability/run/', views.run_manual_calc, name='run_manual_calc'),   
    path('email/download/<str:email_id>/', views.download_email_eml, name='download_email_eml'),
    path('reports/sla/', views.claim_sla_report_view, name='claim_sla_report'),
    path('download-pdf/<int:claim_id>/', views.download_claim_pdf, name='download_claim_pdf'),
]