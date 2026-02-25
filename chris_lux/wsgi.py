"""
WSGI config for Chris Lux project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chris_lux.settings.production')

application = get_wsgi_application()
