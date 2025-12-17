from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # --- Authentication Paths ---
    path('', views.login_view, name='root'), # Mapping root URL to login
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'), # Using custom view for messages/redirect

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
]