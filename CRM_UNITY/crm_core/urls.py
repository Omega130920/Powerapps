# crm_core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # --- Authentication & Dashboard ---
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.login_view, name='root'),

    # --- CRM Member Management ---
    path('global-members/', views.global_members_list, name='global_members_list'),
    path('global-members/<str:member_group_code>/', views.member_information, name='member_information'),
    path('add/member/', views.add_member, name='add_member'),
    path('import/global-data/', views.import_global_data, name='import_global_data'),

    # --- Microsoft Graph Email & Inbox (Automatic Sync) ---
    path('emails/', views.fetch_emails_view, name='fetch_emails'),
    
    # Endpoint for fetching raw HTML content for Modals/Iframes
    path('emails/data/<str:email_id>/', views.get_email_content_view, name='get_email_content'), 
    
    # --- Delegation Workflow ---
    path('emails/delegate/<str:email_id>/', views.delegate_email_view, name='delegate_email'),
    path('tasks/', views.tasks_view, name='tasks'),
    path('tasks/action/<str:email_id>/', views.delegate_action_view, name='delegate_action'),
    path('tasks/send-email/<str:email_id>/', views.send_task_email_view, name='send_task_email'),
    path('tasks/attachment/<str:message_id>/<str:attachment_id>/', 
         views.download_attachment_view, 
         name='download_attachment'),

    # --- Management Overviews (Omega Only Views) ---
    path('delegations-overview/', views.email_registry_view, name='email_registry'),
    path('recycle-bin/', views.recycle_bin_view, name='recycle_bin'),
    path('recycle-bin/delete/', views.delete_recycled_tasks_view, name='delete_recycled'),
    
    # --- Reports & Logs ---
    path('report/', views.delegation_report_view, name='delegation_report'),
    path('complaint-log/', views.complaint_log_view, name='complaint_log'),
    path('thread/<str:email_id>/', views.view_email_thread, name='view_email_thread'),
    
    path('download-attachment/<str:message_id>/<str:attachment_id>/', views.download_attachment_view, name='download_attachment'),
    path('delegation-report/export/', views.export_delegation_report_excel, name='export_delegation_report_excel'),
    path('final-sla-report/', views.final_sla_report_view, name='final_sla_report'),
]