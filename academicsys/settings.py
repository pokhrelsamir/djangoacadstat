import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'dev-secret-key'
DEBUG = True
ALLOWED_HOSTS = [
    'djangoacadstat.vercel.app',
    'localhost',
    '127.0.0.1',

]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core.apps.CoreConfig',
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

ROOT_URLCONF = 'academicsys.urls'

TEMPLATES = [{
'BACKEND': 'django.template.backends.django.DjangoTemplates',
'DIRS': [BASE_DIR / 'templates'],
'APP_DIRS': True,
'OPTIONS': {'context_processors': [
'django.template.context_processors.debug',
'django.template.context_processors.request',
'django.contrib.auth.context_processors.auth',
'django.contrib.messages.context_processors.messages',
]},
}]

WSGI_APPLICATION = 'academicsys.wsgi.application'

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'acadstat',
#         'USER': '',
#         'PASSWORD': '',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'acadstatmain',
        'USER': 'username',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    ]

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Admin custom settings
ADMIN_SITE_HEADER = 'Academic System'
ADMIN_SITE_TITLE = 'Academic Admin'
ADMIN_INDEX_TITLE = 'Dashboard'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '') 
OPENROUTER_API_KEY = 'YOUR API KEY'

OPENROUTER_SITE_URL = os.environ.get('OPENROUTER_SITE_URL', 'http://localhost:8000')
OPENROUTER_SITE_NAME = os.environ.get('OPENROUTER_SITE_NAME', 'AcadStat')

# Email Settings for notifications
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'AcadStat <noreply@acadstat.com>'

# Optional: Twilio for SMS (set these in environment)
# TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
# TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
# TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
