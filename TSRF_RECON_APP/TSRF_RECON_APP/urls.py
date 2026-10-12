# TSRF main project urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from scraper.views import home_view, source_view, games_view, mario_view

# 1. Custom Media Interceptors defined first to prevent default static() blocking
custom_media_patterns = []

if settings.DEBUG:
    from scraper.views import media_directory_explorer
    custom_media_patterns = [
        # Intercepts direct links to the raw root path and forwards them safely to your explorer view
        path('media/planogram_products/', media_directory_explorer, {'subfolder': ''}, name='raw_planogram_root'),
        path('media/planogram_products/<path:subfolder>/', media_directory_explorer, name='raw_planogram_sub'),
        path('media/', media_directory_explorer, {'subfolder': ''}, name='raw_media_root_explorer'),
    ]

# 2. Main core app URL configurations
urlpatterns = custom_media_patterns + [
    path('admin/', admin.site.urls),
    
    # This keeps your live TSRF working exactly as it does now
    path('', include('tsrf_recon.urls')),
    
    # These add the planogram/scraper views under the exact same web address
    path('planogram/', home_view, name='scraper_home'), 
    path('planogram/source/', source_view, name='source'),   
    path('planogram/api/', include('scraper.urls')), 
    path('planogram/games.html', games_view, name='games'),
    path('planogram/supermario.html', mario_view, name='supermario'),
]

if settings.DEBUG:
    from scraper.views import media_directory_explorer
    
    # 🎯 ALIAS MATCHING FIX:
    # Updating names to 'media_root_explorer' and 'media_subfolder_explorer'
    # so that home.html {% url 'media_root_explorer' %} resolves instantly.
    urlpatterns = [
        path('media/planogram_products/', media_directory_explorer, {'subfolder': 'planogram_products'}, name='override_plano_root'),
        path('media/planogram_products/<path:subfolder>/', media_directory_explorer, name='override_plano_sub'),
        
        # Core storage access node mappings expected by home template tags
        path('media/', media_directory_explorer, {'subfolder': ''}, name='media_root_explorer'),
        path('media/<path:subfolder>/', media_directory_explorer, name='media_subfolder_explorer'),
    ] + urlpatterns
    
    # Native asset stream engine layer
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)