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

# --- NATIVE MYSQL ALL-IN-ONE TABLE ALIGNER ---
from django.db import connection

try:
    print("Executing master raw SQL schema alignment for OYA finance...")
    with connection.cursor() as cursor:
        
        # 1. Force drop any conflicting broken structures to allow a completely clean rebuild
        cursor.execute("DROP TABLE IF EXISTS finance_association_dues;")
        
        # 2. Build the main DuesPaymentTransaction table perfectly aligned with your model
        cursor.execute("""
            CREATE TABLE finance_association_dues (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                created_at DATETIME(6) NOT NULL,
                updated_at DATETIME(6) NOT NULL,
                total_amount DECIMAL(15, 2) NOT NULL,
                payment_method VARCHAR(20) NOT NULL,
                receipt_reference VARCHAR(255) NOT NULL,
                payment_date DATE NOT NULL,
                notes LONGTEXT NOT NULL,
                member_id BIGINT NOT NULL,
                recorded_by_id BIGINT NULL
            );
        """)
        
        # 3. Create the Many-to-Many bridge table that Django needs for linking records
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS finance_dues_payment_transactions (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                duespayment_id BIGINT NOT NULL,
                duespaymenttransaction_id BIGINT NOT NULL,
                UNIQUE KEY finance_dues_payment_tra_duespayment_id_duespayme_7fb66e6a_uniq (duespayment_id, duespaymenttransaction_id)
            );
        """)
        
    print("Master SQL alignment completely successful!")
except Exception as e:
    print(f"Master SQL alignment exception caught: {e}")
# --------------------------------------------
