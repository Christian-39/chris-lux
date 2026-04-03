"""
Products Models - Product Catalog, Categories, Reviews
"""
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
import uuid


class Category(models.Model):
    """Product Category Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="FontAwesome icon class")
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='subcategories'
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()
    
    @property
    def full_path(self):
        """Get full category path"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


class Brand(models.Model):
    """Product Brand Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    """Product Model"""
    
    # Stock Status
    STOCK_STATUS_CHOICES = [
        ('in_stock', 'In Stock'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('coming_soon', 'Coming Soon'),
        ('pre_order', 'Pre-Order'),
    ]
    
    # Condition
    CONDITION_CHOICES = [
        ('new', 'Brand New'),
        ('refurbished', 'Refurbished'),
        ('used', 'Used'),
        ('open_box', 'Open Box'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField(max_length=50, unique=True, verbose_name='SKU')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    
    # Relationships
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='products'
    )
    
    # Pricing
    price = models.DecimalField(max_digits=12, decimal_places=2)
    compare_at_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Original price before discount"
    )
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Cost price for profit calculation"
    )
    
    # Inventory
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    stock_status = models.CharField(
        max_length=20,
        choices=STOCK_STATUS_CHOICES,
        default='in_stock'
    )
    
    # Product Details
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='new'
    )
    short_description = models.TextField(
        max_length=500,
        help_text="Brief product summary for listings"
    )
    description = models.TextField(help_text="Full product description")
    key_highlights = models.JSONField(
        default=list,
        blank=True,
        help_text="List of key features/bullet points"
    )
    specifications = models.JSONField(
        default=dict,
        blank=True,
        help_text="Product specifications as key-value pairs"
    )
    
    # Media
    video_url = models.URLField(blank=True, null=True)
    video_file = models.FileField(
        upload_to='products/videos/',
        blank=True,
        null=True
    )
    
    # Status & Visibility
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_hot_deal = models.BooleanField(default=False)
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=500, blank=True, null=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    sales_count = models.PositiveIntegerField(default=0)
    wishlist_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['brand', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            self.sku = f"PRD-{self.id.hex[:8].upper()}"
        
        # Auto-update stock status
        if self.quantity <= 0:
            self.stock_status = 'out_of_stock'
        elif self.quantity <= self.low_stock_threshold:
            self.stock_status = 'low_stock'
        else:
            self.stock_status = 'in_stock'
        
        # Set published date when product becomes active
        if self.is_active and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.compare_at_price and self.compare_at_price > self.price:
            return int(((self.compare_at_price - self.price) / self.compare_at_price) * 100)
        return 0
    
    @property
    def is_on_sale(self):
        """Check if product is on sale"""
        return self.compare_at_price and self.compare_at_price > self.price
    
    @property
    def primary_image(self):
        """Get primary product image"""
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()
    
    @property
    def average_rating(self):
        """Calculate average rating"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0
    
    @property
    def review_count(self):
        """Get approved review count"""
        return self.reviews.filter(is_approved=True).count()
    
    @property
    def in_stock(self):
        """Check if product is in stock"""
        return self.stock_status in ['in_stock', 'low_stock']
    
    def increment_view(self):
        """Increment view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])


class ProductImage(models.Model):
    """Product Image Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='products/images/')
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['is_primary', 'display_order', 'created_at']
    
    def __str__(self):
        return f"{self.product.name} - Image {self.display_order or 1}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(product=self.product).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductReview(models.Model):
    """Product Review Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=255, blank=True, null=True)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.product.name} ({self.rating}★)"


class Wishlist(models.Model):
    """User Wishlist Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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
        ordering = ['-created_at']
        unique_together = ['user', 'product']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update product wishlist count
        self.product.wishlist_count = Wishlist.objects.filter(product=self.product).count()
        self.product.save(update_fields=['wishlist_count'])
    
    def delete(self, *args, **kwargs):
        product = self.product
        super().delete(*args, **kwargs)
        # Update product wishlist count
        product.wishlist_count = Wishlist.objects.filter(product=product).count()
        product.save(update_fields=['wishlist_count'])


class RecentlyViewed(models.Model):
    """Recently Viewed Products Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recently_viewed'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='recently_viewed_by'
    )
    viewed_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-viewed_at']
        unique_together = ['user', 'product']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.product.name}"


class Coupon(models.Model):
    """Coupon/Discount Code Model"""
    
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage'
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    maximum_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    usage_limit = models.PositiveIntegerField(blank=True, null=True)
    usage_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    applicable_products = models.ManyToManyField(
        Product,
        blank=True,
        related_name='applicable_coupons'
    )
    applicable_categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='applicable_coupons'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.code
    
    @property
    def is_valid(self):
        """Check if coupon is currently valid"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from > now:
            return False
        if self.valid_until < now:
            return False
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False
        return True
    
    def calculate_discount(self, subtotal):
        """Calculate discount amount for given subtotal"""
        if subtotal < self.minimum_order_amount:
            return 0
        
        if self.discount_type == 'percentage':
            discount = (subtotal * self.discount_value) / 100
        else:
            discount = self.discount_value
        
        if self.maximum_discount:
            discount = min(discount, self.maximum_discount)
        
        return discount


class FlashSale(models.Model):
    """Flash Sale Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='flash_sales'
    )
    sale_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_limit = models.PositiveIntegerField(blank=True, null=True)
    quantity_sold = models.PositiveIntegerField(default=0)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-starts_at']
    
    def __str__(self):
        return f"{self.product.name} - Flash Sale"
    
    @property
    def is_live(self):
        """Check if flash sale is currently live"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.starts_at > now:
            return False
        if self.ends_at < now:
            return False
        if self.quantity_limit and self.quantity_sold >= self.quantity_limit:
            return False
        return True
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.product.price > self.sale_price:
            return int(((self.product.price - self.sale_price) / self.product.price) * 100)
        return 0
    
    @property
    def time_remaining(self):
        """Get time remaining for flash sale"""
        now = timezone.now()
        if self.ends_at > now:
            return self.ends_at - now
        return None
