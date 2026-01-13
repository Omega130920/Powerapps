"""
URL configuration for consulting_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # This makes the root URL (http://127.0.0.1:8000/) the login page
    path('', auth_views.LoginView.as_view(template_name='consulting/login.html'), name='login'),
    
    # All other consulting app URLs (Dashboard, Calendar, etc.)
    path('consulting/', include('consulting.urls')),
    
    path('accounts/', include('django.contrib.auth.urls')), 
]