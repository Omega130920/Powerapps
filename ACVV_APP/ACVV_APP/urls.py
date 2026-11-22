"""
URL configuration for ACVV_APP project.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from acvv import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('acvv.urls')),

    # Protect all /media/ files behind @login_required (prevents unauthenticated POPIA exposure)
    re_path(r'^media/(?P<path>.*)$', views.protected_media_serve, name='protected_media_serve'),

    # Backward-compatible @login_required routes for legacy upload paths saved before MEDIA_URL = '/media/'
    re_path(
        r'^(?P<path>(?:branch_docs|notes|notes_attachments|claim_attachments|email_attachments)/.*)$',
        views.protected_media_serve,
    ),

    # Static assets (CSS/JS/images) when DEBUG = False
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]