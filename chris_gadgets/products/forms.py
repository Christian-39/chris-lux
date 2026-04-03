from django import forms
from .models import Product, Category

# In products/forms.py

class ProductForm(forms.ModelForm):
    """Product Form with proper widgets"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'short_description', 'description',
            'price', 'compare_at_price', 'cost_price',
            'sku', 'quantity', 'low_stock_threshold',
            'category', 'brand', 'is_active', 'is_featured',
            'is_new_arrival', 'is_hot_deal',
            'meta_title', 'meta_description', 'meta_keywords',
            'condition', 'video_url', 'key_highlights'
            # Removed 'specifications' - handled manually in view
        ]
        widgets = {
            # ... your widgets ...
            'key_highlights': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Enter key features, one per line'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ... your existing __init__ code ...
        
        # key_highlights is JSONField but we'll handle it as text
        self.fields['key_highlights'].required = False