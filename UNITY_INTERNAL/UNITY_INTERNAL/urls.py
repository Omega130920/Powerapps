from django.contrib import admin
from django.urls import path, include
from unity_internal_app.views import index, login_view

# 1. Add these two imports
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('unity_internal_app.urls')),
    path('accounts/login/', login_view, name='login'),
]

# 2. Add this block at the very bottom (outside the list)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)