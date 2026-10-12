from django.urls import path
from .views import automated_planogram_upload

urlpatterns = [
    path('fetch-product/', automated_planogram_upload, name='fetch_product'),
    
]