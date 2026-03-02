"""
Development settings for Chris Lux project.
"""

from .base import *
from decouple import config
import dj_database_url
import environ
import os


env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Cloudinary Config (Get these from your Cloudinary Dashboard)

# Database
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

# Static files - development
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# Media files - development
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Debug Toolbar (optional)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
