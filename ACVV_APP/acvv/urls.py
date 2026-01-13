from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # --- Authentication Paths ---
    path('', views.login_view, name='root'), 
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'), 

    # --- ACVV App Paths (Existing) ---
    path('acvv-records/', views.acvv_list, name='acvv_list'),
    path('acvv-records/<str:mip_names>/', views.acvv_information, name='acvv_information'),
    
    # --- Outlook DELEGATOR Paths (Inbox & Assignment) ---
    path('outlook/', views.outlook_dashboard_view, name='outlook_dashboard'), 
    path('outlook/send/', views.send_email_view, name='send_email'), 
    
    # --- Outlook DELEGATED Paths (Assigned User Workflow) ---
    path('outlook/delegated/', views.outlook_delegated_box, name='outlook_delegated_box'),
    path('outlook/delegated/<int:delegation_id>/action/', 
         views.outlook_delegated_action, 
         name='outlook_delegated_action'),
    path('outlook/delegate/<str:email_id>/', views.outlook_delegate_to, name='outlook_delegate_to'),
    
    # --- Global Claims & Two-Pot Management ---
    path('global-claims/', views.global_claims_view, name='global_claims'),
    path('two-pot-global/', views.global_two_pot_view, name='two_pot_claims'),
    path('save-global-claim/', views.save_global_claim, name='save_global_claim'),
    path('export-claims-excel/', views.export_global_claims_excel, name='export_global_claims_excel'),
    path('acvv-records/<str:company_code>/save-claim/', views.save_acvv_claim, name='save_acvv_claim'),
    
    # --- Recycle Bin ---
    path('recycle-bin/', views.recycle_bin_view, name='recycle_bin'),
    path('recycle-bin/delete/<int:delegation_id>/', views.delete_recycled_item, name='delete_recycled_item'),
    path('recycle-bin/view/<int:delegation_id>/', views.view_recycled_item, name='view_recycled_item'),
    path('recycle-bin/restore/<int:delegation_id>/', views.restore_recycled_item, name='restore_recycled_item'),
    path('recycle-bin/bulk-delete/', views.bulk_delete_recycled, name='bulk_delete_recycled'),
    
    # --- Exports & Utilities ---
    path('acvv/export/', views.export_acvv_list_excel, name='export_acvv_excel'),
    path('outlook/thread/<int:delegation_id>/', views.outlook_view_thread, name='outlook_view_thread'),
    path('export/temp-exists/', views.export_temp_exists, name='export_temp_exists'), #
    
    # --- Reconciliation Worksheet Paths ---
    #
    path('reconciliation-worksheet/', views.reconciliation_worksheet, name='reconciliation_worksheet'),
    path('reconciliation-worksheet/export/<str:date_str>/', 
         views.export_reconciliation_worksheet, 
         name='export_reconciliation_worksheet'),
    path('outlook/email-list/', views.outlook_email_list, name='outlook_email_list'),
]