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

# --- NATIVE MY-SQL DIRECT TABLE INJECTOR ---
from django.db import connection

try:
    print("Attempting direct raw SQL table injection...")
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS finance_association_dues (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                amount DECIMAL(15, 2) NOT NULL,
                payment_method VARCHAR(50) NOT NULL,
                receipt_number VARCHAR(255) NULL,
                created_at DATETIME(6) NOT NULL,
                member_id BIGINT NOT NULL
            );
        """)
    print("Raw SQL table checked/created successfully!")
except Exception as e:
    print(f"Raw SQL injection message: {e}")
# --------------------------------------------
