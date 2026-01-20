import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-eqv3)lf)ob3%mvhf8$h#ow+7ya3zzq0$2c4lkl=yh9)jdixt-q'

DEBUG = True

ALLOWED_HOSTS = ['*','pssubf.futurasa.co.za']
# Modified for development flexibility


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
        # Change DIRS to this to be 100% sure:
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
# Ensure you have 'mysqlclient' or 'django-mysql' installed

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'pssubf_db',
        'USER': 'root',
        'PASSWORD': '13Sept2020@',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}


# --- Microsoft Graph API Settings (Outlook) ---

MSGRAPH_CLIENT_ID = 'your-client-id-here'
MSGRAPH_CLIENT_SECRET = 'your-client-secret-here'
MSGRAPH_TENANT_ID = 'your-tenant-id-here'

# The service account email specifically for PSSUBF
OUTLOOK_EMAIL_ADDRESS = 'pssubf_service@futurasa.co.za'

# Required for the service layer logic
GRAPH_SCOPES = ['https://graph.microsoft.com/.default']


# --- Password validation ---

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Internationalization ---

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Johannesburg' # Updated to local time
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
LOGIN_REDIRECT_URL = 'dashboard'
LOGIN_URL = 'login'

MSGRAPH_CLIENT_ID = '9f82e57d-45a4-4b66-ab29-8a9b381a082a'
MSGRAPH_CLIENT_SECRET = 'PA38Q~14Js~5d7juZm6HjhK8bSOyXDg6ZtdVFdg~'
MSGRAPH_TENANT_ID = '7bcfc080-e1f1-4f99-b4ed-e1a96eda89ce'
OUTLOOK_EMAIL_ADDRESS = 'testuser@futurasa.co.za'