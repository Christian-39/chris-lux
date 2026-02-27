"""
Development settings for Chris Lux project.
"""

from .base import *
from decouple import config
import dj_database_url
import environ


env = environ.Env()
environ.Env.read_env()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Database
DATABASES =  {
    'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
}

# Static files - development
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

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
