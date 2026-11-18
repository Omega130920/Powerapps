from django.contrib import admin
from django.urls import path, include, re_path
from unity_internal_app import views
from unity_internal_app.views import index, login_view

from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('unity_internal_app.urls')),
    path('accounts/login/', login_view, name='login'),
    # Protect all /media/ files behind @login_required to prevent unauthenticated POPIA exposure
    re_path(r'^media/(?P<path>.*)$', views.protected_media_serve, name='protected_media_serve'),
]

# Standard static (CSS/JS) serving only — NEVER serve MEDIA_URL publicly
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=getattr(settings, 'STATIC_ROOT', None))
else:
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': getattr(settings, 'STATIC_ROOT', None)}),
    ]