"""
Orders Models - Shopping Cart, Orders, Order Items
"""
from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import uuid

 
class Cart(models.Model):
    """Shopping Cart Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        blank=True,
        null=True
    )
    session_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.user:
            return f"Cart - {self.user.get_full_name()}"
        return f"Cart - {self.session_id}"
    
    @property
    def item_count(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        """Calculate cart subtotal"""
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def total(self):
        """Calculate cart total (with any applicable discounts)"""
        return self.subtotal
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()


class CartItem(models.Model):
    """Cart Item Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-added_at']
        unique_together = ['cart', 'product']
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    @property
    def subtotal(self):
        """Calculate item subtotal"""
        # Check for flash sale
        flash_sale = self.product.flash_sales.filter(
            is_active=True,
            starts_at__lte=timezone.now(),
            ends_at__gte=timezone.now()
        ).first()
        
        if flash_sale and flash_sale.is_live:
            price = flash_sale.sale_price
        else:
            price = self.product.price
        
        return price * self.quantity
    
    def clean(self):
        """Validate quantity doesn't exceed available stock"""
        from django.core.exceptions import ValidationError
        if self.quantity > self.product.quantity:
            raise ValidationError(
                f"Only {self.product.quantity} items available in stock."
            )


class Order(models.Model):
    """Order Model"""
    
    # Order Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Payment Status
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('awaiting_verification', 'Awaiting Verification'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # User Information
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    
    # Order Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    payment_status = models.CharField(
        max_length=25,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    # Shipping Address
    shipping_name = models.CharField(max_length=255)
    shipping_phone = models.CharField(max_length=17)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=50)
    shipping_lga = models.CharField(max_length=100)
    shipping_landmark = models.CharField(max_length=255, blank=True, null=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Pricing
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Coupon
    coupon = models.ForeignKey(
        'products.Coupon',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='orders'
    )
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    
    # Notes
    customer_note = models.TextField(blank=True, null=True)
    admin_note = models.TextField(blank=True, null=True)
    
    # Tracking
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipping_carrier = models.CharField(max_length=100, blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            today = timezone.now().strftime('%Y%m%d')
            last_order = Order.objects.filter(
                order_number__startswith=f"ORD-{today}"
            ).order_by('-order_number').first()
            
            if last_order:
                last_number = int(last_order.order_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.order_number = f"ORD-{today}-{new_number:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def item_count(self):
        """Get total number of items in order"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def can_cancel(self):
        """Check if order can be cancelled"""
        return self.status in ['pending', 'confirmed']
    
    @property
    def can_track(self):
        """Check if order can be tracked"""
        return self.status in ['shipped', 'out_for_delivery', 'delivered']
    
    @property
    def status_display_class(self):
        """Get CSS class for status badge"""
        status_classes = {
            'pending': 'warning',
            'confirmed': 'info',
            'processing': 'info',
            'shipped': 'primary',
            'out_for_delivery': 'primary',
            'delivered': 'success',
            'cancelled': 'danger',
            'refunded': 'secondary',
        }
        return status_classes.get(self.status, 'secondary')
    
    @property
    def payment_status_display_class(self):
        """Get CSS class for payment status badge"""
        status_classes = {
            'pending': 'warning',
            'awaiting_verification': 'info',
            'verified': 'success',
            'failed': 'danger',
            'refunded': 'secondary',
        }
        return status_classes.get(self.payment_status, 'secondary')


class OrderItem(models.Model):
    """Order Item Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=50)
    product_image = models.URLField(blank=True, null=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        ordering = ['-id']
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """Order Status History Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Order Status Histories'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order.order_number} - {self.status}"


class SavedCart(models.Model):
    """Saved Cart for Later Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_carts'
    )
    name = models.CharField(max_length=100, default='Saved Cart')
    items = models.JSONField(default=list)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.name}"


class FrequentlyBoughtTogether(models.Model):
    """Frequently Bought Together Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    primary_product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='frequently_bought_with'
    )
    related_product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='frequently_bought_as'
    )
    frequency = models.PositiveIntegerField(default=0)
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Discount when bought together"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Frequently Bought Together'
        unique_together = ['primary_product', 'related_product']
        ordering = ['-frequency']
    
    def __str__(self):
        return f"{self.primary_product.name} + {self.related_product.name}"
    
    @property
    def bundle_price(self):
        """Calculate bundle price with discount"""
        total = self.primary_product.price + self.related_product.price
        discount = (total * self.discount_percentage) / 100
        return total - discount
