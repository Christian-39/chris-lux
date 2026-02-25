"""
Reviews forms for Chris Lux.
"""

from django import forms
from .models import Review, ReviewImage


class ReviewForm(forms.ModelForm):
    """Product review form."""
    rating = forms.ChoiceField(
        choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'rating-input'})
    )
    title = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Review Title (Optional)'
        })
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Share your experience with this product...',
            'rows': 5
        })
    )
    
    class Meta:
        model = Review
        fields = ['rating', 'title', 'content']


class ReviewImageForm(forms.ModelForm):
    """Review image form."""
    class Meta:
        model = ReviewImage
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'multiple': False})
        }
