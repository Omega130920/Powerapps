from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# Import the built-in auth views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- ADD THESE AUTH URLS ---
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # ---------------------------

    path('pssubf/', include('PSSUBF_APP.urls')),
    path('', include('PSSUBF_APP.urls')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)