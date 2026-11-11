import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from a local .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

# --- Secure API Integrations & Core Settings ---
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-eqv3)lf)ob3%mvhf8$h#ow+7ya3zzq0$2c4lkl=yh9)jdixt-q')

DEBUG = False

ALLOWED_HOSTS = ['*', 'pssubf.futurasa.co.za', 'pssubf.futura.co.za']

# 1. Trust the secure domain for form submissions
CSRF_TRUSTED_ORIGINS = [
    'https://pssubf.futurasa.co.za',
    'https://pssubf.futura.co.za', 
]

# 2. Handle the Proxy headers from your hoster (Critical for SSL)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 3. Security tweaks for HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# --- Application definition ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Custom Apps
    'PSSUBF_APP',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'PSSUBF_PORTAL.urls'

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

WSGI_APPLICATION = 'PSSUBF_PORTAL.wsgi.application'


# --- Database Configuration (MySQL for Unmanaged Models) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'pssubf_db',
        'USER': os.environ.get('DB_USER', 'pssubf_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# --- Microsoft Graph API Settings (Outlook) ---
MSGRAPH_CLIENT_ID = os.environ.get('MSGRAPH_CLIENT_ID', '')
MSGRAPH_CLIENT_SECRET = os.environ.get('MSGRAPH_CLIENT_SECRET', '')
MSGRAPH_TENANT_ID = os.environ.get('MSGRAPH_TENANT_ID', '')

# The service account email specifically for PSSUBF
OUTLOOK_EMAIL_ADDRESS = 'pssbf@futurasa.co.za'

# Required for the service layer logic
GRAPH_SCOPES = ['https://graph.microsoft.com/.default']

WINSMS_API_KEY = os.environ.get('WINSMS_API_KEY', '')


# --- Password validation ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Internationalization ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Johannesburg' 
USE_I18N = True
USE_TZ = True


# --- Static & Media Files ---
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'assets')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login Redirects
LOGIN_REDIRECT_URL = 'pssubf_switchboard'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'login'