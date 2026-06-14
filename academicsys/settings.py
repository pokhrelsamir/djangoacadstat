import os
from pathlib import Path
from django.templatetags.static import static

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'dev-secret-key'
DEBUG = True
ALLOWED_HOSTS = [
    'djangoacadstat.vercel.app',
    'localhost',
    '127.0.0.1',
]

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.inlines',
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

# PostgreSQL Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'acadstat',
        'USER': 'sajit',
       # 'USER': 'shreeadhikari',
        'PASSWORD': 'acadstat',
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
