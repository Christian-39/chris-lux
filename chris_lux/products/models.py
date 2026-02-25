"""
Products models for Chris Lux.
"""

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    """Product category model."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})
    
    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    """Product model."""
    # Basic info
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    sku = models.CharField(max_length=50, unique=True, blank=True)
    description = models.TextField()
    short_description = models.TextField(blank=True)
    
    # Categorization
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    tags = models.CharField(max_length=300, blank=True, help_text="Comma-separated tags")
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    track_stock = models.BooleanField(default=True)
    allow_backorders = models.BooleanField(default=False)
    
    # Variations
    has_variations = models.BooleanField(default=False)
    
    # Shipping
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text="Weight in kg")
    
    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    # Display options
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    is_new = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            self.sku = f"CLX{self.id or Product.objects.count() + 1:05d}"
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})
    
    @property
    def is_in_stock(self):
        if not self.track_stock:
            return True
        if self.has_variations:
            return any(v.stock_quantity > 0 for v in self.variations.all())
        return self.stock_quantity > 0 or self.allow_backorders
    
    @property
    def display_price(self):
        if self.has_variations:
            variations = self.variations.filter(is_active=True)
            if variations.exists():
                prices = [v.price for v in variations]
                if prices:
                    min_price = min(prices)
                    max_price = max(prices)
                    if min_price == max_price:
                        return min_price
                    return f"{min_price} - {max_price}"
        return self.price
    
    @property
    def discount_percentage(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return int(((self.compare_at_price - self.price) / self.compare_at_price) * 100)
        return 0
    
    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0
    
    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()
    
    @property
    def primary_image(self):
        images = self.images.filter(is_primary=True)
        if images.exists():
            return images.first()
        images = self.images.all()
        if images.exists():
            return images.first()
        return None


class ProductImage(models.Model):
    """Product image gallery."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.product.name} - Image {self.order + 1}"
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            # Ensure only one primary image per product
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class Variation(models.Model):
    """Product variation model (length, texture, color, etc.)."""
    VARIATION_TYPES = [
        ('length', 'Length'),
        ('texture', 'Texture'),
        ('color', 'Color'),
        ('size', 'Size'),
        ('style', 'Style'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variations')
    variation_type = models.CharField(max_length=20, choices=VARIATION_TYPES)
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=50)
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Variation'
        verbose_name_plural = 'Variations'
        unique_together = ['product', 'variation_type', 'value']
        ordering = ['variation_type', 'value']
    
    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"
    
    @property
    def final_price(self):
        return self.product.price + self.price_adjustment
