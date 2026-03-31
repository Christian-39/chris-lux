#!/bin/bash

# Build script for Chris-Lux Django Application

echo "Building Chris-Lux Django Application..."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create default site settings
echo "Setting up default site settings..."
python -c "
import django
django.setup()
from settings_app.models import SiteSettings
if not SiteSettings.objects.exists():
    SiteSettings.objects.create(
        site_name='Chris-Lux',
        site_tagline='Premium Hair Extensions & Wigs',
        contact_email='support@chris-lux.com'
    )
    print('Default site settings created.')
"

echo "Build completed successfully!"
