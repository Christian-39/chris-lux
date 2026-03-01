"""
Production settings for Chris Lux project.
"""

from .base import *
import dj_database_url
from decouple import config
import os


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# Cloudinary Config (Get these from your Cloudinary Dashboard)
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET')
}
# Database - MySQL
DATABASES = {
    'default': dj_database_url.config(
        # 1. On Render: Uses the high-speed DATABASE_URL
        # 2. Locally: If no URL is found, it creates/uses local db.sqlite3
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
        # Only require SSL if we aren't using SQLite (SQLite doesn't support SSL)
        ssl_require=config('DATABASE_URL', default='').startswith('postgres')
    )
}

# Static files - production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# This tells Django where to send uploaded files
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Security Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Logging
import os

LOGS_DIR = BASE_DIR / 'logs'
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'django_error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}


ADMINS = [
    ('Admin', config('ADMIN_EMAIL', default='admin@chrislux.com')),
]

