from django.db import migrations

class Migration(migrations.migrations.Migration):

    dependencies = [
        # CRITICAL: Replace '0003_previous_file_name' with the exact name 
        # of your last migration file in this folder (minus the .py extension)
        ('finance', '0002_income_add_member'),
    ]

    operations = [
        # We leave this completely empty! 
        # This tells Django to record the file as "done" without executing any SQL queries.
    ]
