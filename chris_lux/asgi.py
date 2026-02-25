"""
ASGI config for Chris Lux project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chris_lux.settings.production')

application = get_asgi_application()
