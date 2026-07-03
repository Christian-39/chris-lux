from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        # This points back to your previous valid migration file
                ('finance', '0002_income_add_member'), 
    ]

    operations = [
        # Left empty on purpose to bypass trying to create your manual table!
    ]
