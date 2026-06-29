"""
Django settings for OYA project.

Okpo Youths Association Management System
"""

import os
from decouple import config
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-me-in-production-oy4-kp0-y0uth5-@550c!@t!0n",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

LOCAL_APPS = [
    "core",
    "accounts",
    "members",
    "executives",
    "elections",
    "finance",
    "projects",
    "operations",
    "notifications",
    "auditlogs",
    "dashboard",
    "settingsapp",
]

THIRD_PARTY_APPS = []

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.AuditLogMiddleware",
    "core.middleware.ExceptionHandlerMiddleware",
]

ROOT_URLCONF = "oya.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "settingsapp.context_processors.system_settings",
                "notifications.context_processors.unread_notifications",
                "core.context_processors.user_member",
            ],
        },
    },
]

WSGI_APPLICATION = "oya.wsgi.application"
ASGI_APPLICATION = "oya.asgi.application"

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=BASE_DIR / 'db.sqlite3'),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 6,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Custom User Model
AUTH_USER_MODEL = "accounts.User"

# Authentication backends
AUTHENTICATION_BACKENDS = [
    "accounts.backends.SerialNumberAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Lagos"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media & Storage Configuration
MEDIA_STORAGE_MODE = config("MEDIA_STORAGE_MODE", "local")

if MEDIA_STORAGE_MODE == "b2":
    # Backblaze B2 Production Settings
    B2_KEY_ID = config("B2_KEY_ID")
    B2_APPLICATION_KEY = config("B2_APPLICATION_KEY")
    B2_BUCKET_NAME = config("B2_BUCKET_NAME")
    B2_BUCKET_REGION = config("B2_BUCKET_REGION", "us-west-004")
    B2_ENDPOINT_URL = config("B2_ENDPOINT_URL")
    B2_CUSTOM_DOMAIN = config("B2_CUSTOM_DOMAIN", None)
    
    AWS_ACCESS_KEY_ID = B2_KEY_ID
    AWS_SECRET_ACCESS_KEY = B2_APPLICATION_KEY
    AWS_STORAGE_BUCKET_NAME = B2_BUCKET_NAME
    AWS_S3_REGION_NAME = B2_BUCKET_REGION
    AWS_S3_ENDPOINT_URL = B2_ENDPOINT_URL
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_DEFAULT_ACL = None
    AWS_S3_VERIFY = True
    
    if B2_CUSTOM_DOMAIN:
        AWS_S3_CUSTOM_DOMAIN = B2_CUSTOM_DOMAIN.replace("https://", "").replace("http://", "")
    
    MEDIA_URL = f"https://{B2_CUSTOM_DOMAIN}/media/" if B2_CUSTOM_DOMAIN else f"{B2_ENDPOINT_URL}/{B2_BUCKET_NAME}/media/"
    
    STORAGES = {
        "default": {
            "BACKEND": "oya.storage_backends.BackblazeB2Storage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    # Local storage for development
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"
    
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

# Whitenoise for static files in production
if not DEBUG:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
    STORAGES["staticfiles"] = {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    }

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Login settings
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Logging
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "oya.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "oya_errors.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": True,
        },
        "oya": {
            "handlers": ["file", "error_file", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Cache settings
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "oya-cache",
        "TIMEOUT": 300,  # 5 minutes
    }
}

# Celery settings
CELERY_BROKER_URL = config("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# OYA-specific settings
OYA_SETTINGS = {
    "MEMBER_MIN_AGE": 18,
    "PAST_MEMBER_AGE": 56,
    "ELECTION_CYCLE_YEARS": 4,
    "CURRENCY_SYMBOL": "\u20a6",  # Naira symbol
    "SERIAL_NUMBER_PREFIX": "OYA",
}
