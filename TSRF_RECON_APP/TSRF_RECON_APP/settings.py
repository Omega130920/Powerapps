import os
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv() 

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Explicitly set OAUTHLIB_INSECURE_TRANSPORT for local HTTP testing
if os.getenv('DJANGO_ENV', 'development') == 'development' or DEBUG:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Application definition
INSTALLED_APPS = [
    'tsrf_recon', 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware', # Keep disabled if handling legacy PowerApp POSTs
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'TSRF_RECON_APP.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'TSRF_RECON_APP.wsgi.application'

# Database - MySQL Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'), 
        'USER': os.getenv('DB_USER'), 
        'PASSWORD': os.getenv('DB_PASSWORD'), 
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth Redirects
LOGIN_REDIRECT_URL = 'dashboard'
LOGIN_URL = 'login'

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ==============================================================================
# 🔑 MICROSOFT GRAPH API SETTINGS (OUTLOOK) - UNIFIED FOR TSRF_RECON_APP
# ------------------------------------------------------------------------------
# These names match exactly what views.py and the Graph Service expect.
# ==============================================================================

# TSRF_RECON_APP/settings.py

# ... (Authentication/Load dotenv section) ...

# ==============================================================================
# 🔑 MICROSOFT GRAPH API SETTINGS (OUTLOOK) - CONSOLIDATED FOR TSRF_RECON_APP
# ==============================================================================

# 1. The mailbox address used for delegation
OUTLOOK_EMAIL_ADDRESS = os.getenv('OUTLOOK_EMAIL_ADDRESS')

# 2. Azure App Registration Credentials
# Ensure these variables match the MSGRAPH names expected by the service files
MSGRAPH_CLIENT_ID = os.getenv('MSGRAPH_CLIENT_ID')
MSGRAPH_CLIENT_SECRET = os.getenv('MSGRAPH_CLIENT_SECRET')
MSGRAPH_TENANT_ID = os.getenv('MSGRAPH_TENANT_ID') # <--- CHECK THIS LINE

# 3. Scopes for Microsoft Graph
GRAPH_SCOPES = [
    'https://graph.microsoft.com/.default'
]

# Aliases (Optional, but useful if other code expects the OUTLOOK_ prefix)
# OUTLOOK_CLIENT_ID = MSGRAPH_CLIENT_ID 
# OUTLOOK_CLIENT_SECRET = MSGRAPH_CLIENT_SECRET
# OUTLOOK_TENANT_ID = MSGRAPH_TENANT_ID