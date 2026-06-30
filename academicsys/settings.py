from pathlib import Path
import os
from django.templatetags.static import static

BASE_DIR = Path(__file__).resolve().parent.parent

IS_VERCEL = os.environ.get('VERCEL') == '1'

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'dev-secret-key-for-local-development-only-change-in-production-2026'
)
DEBUG = os.environ.get('DJANGO_DEBUG', 'False' if IS_VERCEL else 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        'DJANGO_ALLOWED_HOSTS',
        'djangoacadstat.vercel.app,.vercel.app,localhost,127.0.0.1'
    ).split(',')
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        'DJANGO_CSRF_TRUSTED_ORIGINS',
        'https://djangoacadstat.vercel.app,https://*.vercel.app'
    ).split(',')
    if origin.strip()
]

if IS_VERCEL:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', str(IS_VERCEL)).lower() in ('true', '1', 'yes')
SESSION_COOKIE_SECURE = os.environ.get('DJANGO_SESSION_COOKIE_SECURE', str(IS_VERCEL)).lower() in ('true', '1', 'yes')
CSRF_COOKIE_SECURE = os.environ.get('DJANGO_CSRF_COOKIE_SECURE', str(IS_VERCEL)).lower() in ('true', '1', 'yes')
SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '31536000' if IS_VERCEL else '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', str(IS_VERCEL)).lower() in ('true', '1', 'yes')
SECURE_HSTS_PRELOAD = os.environ.get('DJANGO_SECURE_HSTS_PRELOAD', str(IS_VERCEL)).lower() in ('true', '1', 'yes')

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.inlines',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # API
    'rest_framework',
    'drf_spectacular',

    # Project
    'core.apps.CoreConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
            'django.template.context_processors.csrf',
        ],
    },
}]

WSGI_APPLICATION = 'academicsys.wsgi.application'

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=os.environ.get('DB_SSL_REQUIRE', 'True').lower() in ('true', '1', 'yes'),
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'acadstatmain'),
            'USER': os.environ.get('POSTGRES_USER', 'samir'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'pass'),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
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
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

ADMIN_SITE_HEADER = 'AcadStat System'
ADMIN_SITE_TITLE = 'AcadStat Admin'
ADMIN_INDEX_TITLE = 'Dashboard'

UNFOLD = {
    'SITE_TITLE': ADMIN_SITE_TITLE,
    'SITE_HEADER': ADMIN_SITE_HEADER,
    'SITE_SUBHEADER': ADMIN_INDEX_TITLE,
    'SITE_URL': '/',
    'SITE_SYMBOL': 'school',
    'SHOW_HISTORY': True,
    'SHOW_VIEW_ON_SITE': True,
    'COLORS': {
        'base': {
            '50': 'oklch(98.5% .002 247.839)',
            '100': 'oklch(96.7% .003 264.542)',
            '200': 'oklch(92.8% .006 264.531)',
            '300': 'oklch(87.2% .01 258.338)',
            '400': 'oklch(70.7% .022 261.325)',
            '500': 'oklch(55.1% .027 264.364)',
            '600': 'oklch(44.6% .03 256.802)',
            '700': 'oklch(37.3% .034 259.733)',
            '800': 'oklch(27.8% .033 256.848)',
            '900': 'oklch(21% .034 264.665)',
            '950': 'oklch(13% .028 261.692)',
        },
        'primary': {
            '50': 'oklch(98.5% .002 247.839)',
            '100': 'oklch(96.7% .003 264.542)',
            '200': 'oklch(92.8% .006 264.531)',
            '300': 'oklch(87.2% .01 258.338)',
            '400': 'oklch(70.7% .022 261.325)',
            '500': 'oklch(21% .034 264.665)',
            '600': 'oklch(21% .034 264.665)',
            '700': 'oklch(13% .028 261.692)',
            '800': 'oklch(13% .028 261.692)',
            '900': 'oklch(13% .028 261.692)',
            '950': 'oklch(13% .028 261.692)',
        },
        'font': {
            'subtle-light': 'var(--color-base-500)',
            'subtle-dark': 'var(--color-base-400)',
            'default-light': 'var(--color-base-600)',
            'default-dark': 'var(--color-base-300)',
            'important-light': 'var(--color-base-950)',
            'important-dark': 'var(--color-base-50)',

        },
    },

    'STYLES': [
        lambda request: static('css/unfold-admin-overrides.css'),
    ],
}

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 
    'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'AcadStat API',
    'DESCRIPTION': 'Academic Management System API',
    'VERSION': '1.0.0',
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

import os as _os

EMAIL_BACKEND = _os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = _os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(_os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = _os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = _os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = _os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
DEFAULT_FROM_EMAIL = _os.environ.get('DEFAULT_FROM_EMAIL', 'AcadStat <noreply@acadstat.com>')

MIDDLEWARE += ['core.middleware.RolePermissionMiddleware']
