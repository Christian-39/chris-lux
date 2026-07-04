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
        # 1. Ensure the base table exists
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
        
        # 2. Safely inject the missing updated_at column if it's not there
        cursor.execute("""
            GLOBAL_ALTER: ALTER TABLE finance_association_dues 
            ADD COLUMN IF NOT EXISTS updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6);
        """)
    print("Raw SQL table and columns updated successfully!")
except Exception as e:
    # If your MySQL version doesn't support 'ADD COLUMN IF NOT EXISTS', catch it cleanly
    try:
        with connection.cursor() as cursor:
            cursor.execute("ALTER TABLE finance_association_dues ADD COLUMN updated_at DATETIME(6) NOT NULL;")
    except Exception as inner_e:
        print(f"Raw SQL injection message: {e} | Inner: {inner_e}")
# --------------------------------------------
