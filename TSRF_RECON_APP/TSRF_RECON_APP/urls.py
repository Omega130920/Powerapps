# TSRF_RECON_APP/urls.py (main project urls.py)

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # All of the project's main URLs are included from the tsrf_recon app.
    path('', include('tsrf_recon.urls')),
]