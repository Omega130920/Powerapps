# tsrf_recon/urls.py (app's urls.py)

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Core authentication and dashboard URLs
    path('', views.login_view, name='root'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),

    # URLs for the Levy Data functionality
    path('levy-data/', views.levy_list, name='levy_list'),
    path('levy-data/<str:levy_number>/', views.levy_information, name='levy_information'),
    path('import/', views.import_data, name='process_import'),
    path('import_org/', views.import_org_data, name='process_org_import'),
    path('org/table/info/<str:levy_number>/', views.org_table_info, name='org_table_info'),
    
    # --- BANK LINE VIEWS ---
    path('banklines/unreconciled/', views.unreconciled_banklines, name='unreconciled_banklines'),
    path('banklines/global-bank/', views.global_bank_view, name='global_bank'),
    
    # --- OTHER VIEWS ---
    path('org-table/', views.org_table_view, name='org_table'),
    path('org-table/', views.org_table_view, name='org_table_view'),
    path('levy/add/', views.add_levy_view, name='add_levy_view'),
    path('banklines/allocate/<int:bank_line_id>/', views.bankline_allocation, name='bankline_allocation'),
    path('levy-data/<path:levy_number>/bankline_edits.html', views.bankline_edits_view, name='bankline_edits'),
    path('add-levy/', views.add_levy_view, name='add_levy'),

    # ==============================================================================
    # 📧 MICROSOFT GRAPH API & DELEGATION ROUTES (TRANSPLANTED)
    # ==============================================================================
    
    # 1. Main Shared Inbox (Admin View)
    path('outlook/inbox/', views.outlook_dashboard_view, name='outlook_dashboard'),
    
    # 2. Delegation Form (Where the Admin assigns the email to an Agent)
    path('outlook/delegate/<str:email_id>/', views.outlook_delegate_to, name='outlook_delegate_to'),
    
    # 3. Agent's Private Task Box (Where Agents see emails assigned to them)
    path('outlook/my-tasks/', views.outlook_delegated_box, name='outlook_delegated_box'),
    
    # 4. Task Action Page (Where Agents reply to emails and add notes)
    path('outlook/task/<int:delegation_id>/', views.outlook_delegated_action, name='outlook_delegated_action'),
    
    # 5. Helper: Fetches raw email HTML for iframes
    path('outlook/content/<str:email_id>/', views.outlook_email_content, name='outlook_email_content'),

    # 6. Direct Send (Optional)
    path('outlook/send/', views.send_email_view, name='send_email'),
    path('outlook/recycle-bin/', views.outlook_recycle_bin, name='outlook_recycle_bin'),
    path('outlook/recycle-bin/delete/', views.outlook_delete_permanent, name='outlook_delete_permanent'),
    path('outlook/recycle-bin/restore/<int:delegation_id>/', views.restore_from_recycle_bin, name='restore_from_recycle_bin'),
    
    path('outlook/compose/', views.outlook_compose, name='outlook_compose'),
    path('banklines/export-csv/', views.export_bank_csv, name='export_bank_csv'),
    path('import-levy/', views.import_levy_data, name='import_levy_excel'),
    path('billing-summary/', views.billing_summary, name='billing_summary'),
    path('levy-info/thread/<int:delegation_id>/', views.view_email_thread, name='view_email_thread'),
    path('attorney-summary/', views.attorney_list, name='attorney_list'),
    path('aod-records/', views.aod_list, name='aod_list'),
    path('pfa-matters/', views.pfa_list, name='pfa_list'),
    path('lpi-records/', views.lpi_list, name='lpi_list'),
    path('import-lpi/', views.import_lpi_excel, name='import_lpi'),
    path('attorney-summary/<str:levy_number>/', views.attorney_case_view, name='attorney_summary_view'),
    path('attorney-summary/<str:levy_number>/add-aod/', views.create_aod, name='create_aod'),
    path('get-attorney-detail/<str:levy_number>/', views.get_attorney_detail_ajax, name='get_attorney_detail_ajax'),
    path('attorney-summary/<str:levy_number>/add-pfa/', views.create_pfa, name='create_pfa'),
    path('get-aod-detail-ajax/<str:aod_number>/', views.get_aod_detail_ajax, name='get_aod_detail_ajax'),
    path('get-pfa-detail-ajax/<str:pfa_number>/', views.get_pfa_detail_ajax, name='get_pfa_detail_ajax'),
    path('export-masterfile/', views.export_masterfile_excel, name='export_masterfile'),
]

# This part ensures media files are accessible in your browser
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)