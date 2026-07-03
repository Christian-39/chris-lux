from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        # Link it straight to 0001 to bypass the 0002 node error
        ('finance', '0001_initial'),
    ]

    operations = [
        # Kept completely empty so it doesn't create any tables
    ]
