# products/context_processors.py
from .models import Category

def nav_categories(request):
    return {
        'nav_categories': Category.objects.all() # Or .filter(is_active=True)
    }