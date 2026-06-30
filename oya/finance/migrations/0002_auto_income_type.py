from django.db import migrations


def set_income_types(apps, schema_editor):
    Income = apps.get_model("finance", "Income")
    
    # Mark records that look like dues
    for income in Income.objects.all():
        reason_lower = income.reason.lower()
        if "dues" in reason_lower or "due" in reason_lower:
            income.income_type = "DUES"
        elif "donation" in reason_lower or "donate" in reason_lower:
            income.income_type = "DONATION"
        elif "event" in reason_lower or "ticket" in reason_lower:
            income.income_type = "EVENT"
        else:
            income.income_type = "OTHER"
        income.save(update_fields=["income_type"])


class Migration(migrations.Migration):
    dependencies = [
        # Replace with your actual last migration name
        ("finance", "000X_previous_migration"),
    ]

    operations = [
        migrations.RunPython(set_income_types),
    ]
