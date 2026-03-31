"""
Order models for Chris-Lux.
"""
from django.db import models
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal


class Cart(models.Model):
    """Shopping cart model."""
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='carts',
        null=True,
        blank=True
    )
    session_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Cart {self.session_id}"
    
    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())
    
    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all())
    
    def get_subtotal(self):
        return self.get_total()
    
    def clear(self):
        """Clear all items from cart."""
        self.items.all().delete()


class CartItem(models.Model):
    """Cart item model."""
    
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
        unique_together = ['cart', 'product']
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def get_subtotal(self):
        return self.product.price * self.quantity
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.product.track_inventory and self.quantity > self.product.stock_quantity:
            raise ValidationError(
                f"Only {self.product.stock_quantity} items available in stock."
            )


class Order(models.Model):
    """Order model."""
    
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('payment_uploaded', 'Payment Uploaded'),
        ('verified', 'Payment Verified'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    SHIPPING_METHODS = [
        ('standard', 'Standard Shipping'),
        ('express', 'Express Shipping'),
        ('overnight', 'Overnight Shipping'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True, blank=True)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    
    # Order status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending_payment'
    )
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Shipping
    shipping_method = models.CharField(
        max_length=20,
        choices=SHIPPING_METHODS,
        default='standard'
    )
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_country = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    tracking_number = models.CharField(max_length=255, blank=True)
    
    # Contact
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Notes
    customer_note = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        
        # Calculate total
        self.total_amount = (
            self.subtotal +
            self.shipping_cost +
            self.tax -
            self.discount
        )
        
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Generate unique order number."""
        timestamp = timezone.now().strftime('%Y%m%d')
        last_order = Order.objects.filter(
            order_number__startswith=f'CL-{timestamp}'
        ).order_by('-order_number').first()
        
        if last_order:
            last_num = int(last_order.order_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f'CL-{timestamp}-{new_num:04d}'
    
    def get_absolute_url(self):
        return reverse('orders:order_detail', kwargs={'pk': self.pk})
    
    @property
    def items_count(self):
        return sum(item.quantity for item in self.items.all())
    
    def can_cancel(self):
        """Check if order can be cancelled."""
        return self.status in ['pending_payment', 'payment_uploaded']
    
    def can_upload_receipt(self):
        """Check if receipt can be uploaded."""
        return self.status == 'pending_payment'


class OrderItem(models.Model):
    """Order item model."""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['-id']
    
    def __str__(self):
        return f"{self.quantity} x {self.product_name}"
    
    def get_subtotal(self):
        return self.price * self.quantity


class OrderStatusHistory(models.Model):
    """Track order status changes."""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Order status histories'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order.order_number}: {self.old_status} -> {self.new_status}"


class Coupon(models.Model):
    """Coupon model for discounts."""
    
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(
        max_length=10,
        choices=[
            ('percentage', 'Percentage'),
            ('fixed', 'Fixed Amount'),
        ]
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    uses_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        """Check if coupon is valid."""
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses and self.uses_count >= self.max_uses:
            return False
        return True
    
    def calculate_discount(self, subtotal):
        """Calculate discount amount."""
        if subtotal < self.minimum_order:
            return Decimal('0')
        
        if self.discount_type == 'percentage':
            discount = subtotal * (self.discount_value / 100)
        else:
            discount = self.discount_value
        
        return min(discount, subtotal)
