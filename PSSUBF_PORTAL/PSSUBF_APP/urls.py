from django.urls import path
from . import views

urlpatterns = [
    # 1. The Main Menu / Switchboard (Renders dashboard.html)
    path('', views.pssubf_switchboard, name='pssubf_switchboard'),
    
    # 2. Live Inbox List (Renders inbox_list.html from pssubf_inbox table)
    path('inbox/', views.pssubf_dashboard, name='pssubf_dashboard'),
    
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
]