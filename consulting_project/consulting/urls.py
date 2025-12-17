from django.urls import path
from . import views 

# This list will hold all the URL patterns for the 'consulting' app
urlpatterns = [
    # Core Application Routes
    path('', views.consulting_home, name='consulting_home'),
    path('home/', views.home_view, name='home'), # Added 'home' name for consistency if used elsewhere
    
    # Client Management Routes
    path('clients/', views.client_list_view, name='client_list'),
    path('client/<str:client_code>/', views.client_info_view, name='client_info'),
    path('clients/add/', views.add_client_view, name='add_client'),
    path('clients/edit/<str:client_code>/', views.edit_client_view, name='edit_client'),

    # Lead Management Routes
    path('leads/', views.lead_list_view, name='lead_list'),
    path('leads/add/', views.add_new_lead_view, name='add_new_lead'),
    path('leads/<int:lead_id>/info/', views.lead_info_view, name='lead_info'),
    path('leads/<int:lead_id>/edit/', views.lead_edit_view, name='edit_lead'),
    
    # Path for logging a new note/follow-up
    path('leads/<int:lead_id>/log_note/', views.log_lead_note_view, name='log_lead_note'),
    # URL for the Claims Dashboard
    path('claims/', views.claims_dashboard, name='claims_dashboard'),
    
    # API endpoint to handle new claim submission
    path('claims/create/', views.create_new_claim, name='create_new_claim'),
    path('claims/add_note/', views.create_claim_note, name='create_claim_note'), 
    path('claims/add_reminder/', views.create_claim_reminder, name='create_claim_reminder'),
    path('claims/update_details/', views.update_claim_details, name='update_claim_details'),
]