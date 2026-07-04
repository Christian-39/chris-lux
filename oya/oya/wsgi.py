"""
WSGI config for OYA project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oya.settings")

application = get_wsgi_application()

# --- EMERGENCY MOBILE DB FORCE ---
import sys
from django.core.management import call_command

try:
    print("Forcing migration engine execution...")
    # This instructs Django to manually run our fresh 0003 migration 
    call_command('migrate', 'finance', '0003_create_dues_table', interactive=False)
    print("Migration executed successfully!")
except Exception as e:
    print(f"Migration fallback message: {e}")
# ----------------------------------
