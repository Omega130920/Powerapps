# tsrf_recon/urls.py (app's urls.py)

from django.urls import path
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
    path('banklines/', views.bank_line_list, name='bank_line_list'),
    path('banklines/allocated/', views.allocated_bank_line_list, name='allocated_bank_line_list'),
    path('banklines/reconciled/', views.assigned_bank_line_list, name='reconciled_bank_line_list'),
    
    # --- OTHER VIEWS ---
    path('org-table/', views.org_table_view, name='org_table'),
    path('org-table/', views.org_table_view, name='org_table_view'),
    path('levy/add/', views.add_levy_view, name='add_levy'),
    path('banklines/allocate/<int:bank_line_id>/', views.bankline_allocation, name='bankline_allocation'),
    path('levy-data/<str:levy_number>/bankline_edits.html', views.bankline_edits_view, name='bankline_edits'),

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
]