"""
Product models for Chris-Lux.
"""
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone


class Category(models.Model):
    """Product category model."""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    """Product model for hair items."""
    
    PRODUCT_TYPES = [
        ('wig', 'Wig'),
        ('bundle', 'Bundle'),
        ('closure', 'Closure'),
        ('frontal', 'Frontal'),
        ('accessory', 'Accessory'),
    ]
    
    HAIR_TEXTURES = [
        ('straight', 'Straight'),
        ('body_wave', 'Body Wave'),
        ('loose_wave', 'Loose Wave'),
        ('deep_wave', 'Deep Wave'),
        ('curly', 'Curly'),
        ('kinky_curly', 'Kinky Curly'),
        ('water_wave', 'Water Wave'),
    ]
    
    HAIR_ORIGINS = [
        ('brazilian', 'Brazilian'),
        ('peruvian', 'Peruvian'),
        ('malaysian', 'Malaysian'),
        ('indian', 'Indian'),
        ('vietnamese', 'Vietnamese'),
        ('mongolian', 'Mongolian'),
    ]
    
    LENGTHS = [
        (8, '8"'), (10, '10"'), (12, '12"'), (14, '14"'),
        (16, '16"'), (18, '18"'), (20, '20"'), (22, '22"'),
        (24, '24"'), (26, '26"'), (28, '28"'), (30, '30"'),
        (32, '32"'), (34, '34"'), (36, '36"'), (38, '38"'), (40, '40"'),
    ]
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=255, blank=True)
    
    # Product details
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )
    
    # Hair specifications
    hair_texture = models.CharField(
        max_length=20,
        choices=HAIR_TEXTURES,
        blank=True
    )
    hair_origin = models.CharField(
        max_length=20,
        choices=HAIR_ORIGINS,
        blank=True
    )
    length = models.PositiveIntegerField(choices=LENGTHS, null=True, blank=True)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    cost_per_item = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    track_inventory = models.BooleanField(default=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['product_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            self.sku = f"CL-{self.id or 'NEW'}-{timezone.now().strftime('%Y%m%d')}"
        if not self.meta_title:
            self.meta_title = self.name
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})
    
    @property
    def is_in_stock(self):
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0
    
    @property
    def has_sale(self):
        return self.compare_at_price and self.compare_at_price > self.price
    
    @property
    def discount_percentage(self):
        if self.has_sale:
            return int(((self.compare_at_price - self.price) / self.compare_at_price) * 100)
        return 0
    
    @property
    def primary_image(self):
        image = self.images.filter(is_primary=True).first()
        if not image:
            image = self.images.first()
        return image
    
    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return reviews.aggregate(avg=models.Avg('rating'))['avg']
        return 0
    
    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()
    
    def get_related_products(self, limit=4):
        """Get related products based on category and type."""
        return Product.objects.filter(
            models.Q(category=self.category) | models.Q(product_type=self.product_type),
            is_active=True
        ).exclude(id=self.id).distinct()[:limit]


class ProductImage(models.Model):
    """Product image model."""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='products/images/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order', 'created_at']
    
    def __str__(self):
        return f"Image for {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductVideo(models.Model):
    """Product video model."""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    video = models.FileField(upload_to='products/videos/')
    thumbnail = models.ImageField(
        upload_to='products/video_thumbnails/',
        blank=True,
        null=True
    )
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order', 'created_at']
    
    def __str__(self):
        return f"Video for {self.product.name}"


class ProductReview(models.Model):
    """Product review model."""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)]
    )
    title = models.CharField(max_length=255, blank=True)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user']
    
    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"


class Wishlist(models.Model):
    """User wishlist model."""
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='wishlist'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s wishlist item: {self.product.name}"
