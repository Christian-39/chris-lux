"""
Cart models for Chris Lux.
"""

from django.db import models
from django.conf import settings
from chris_lux.products.models import Product, Variation


class Cart(models.Model):
    """Shopping cart model."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart'
    )
    session_id = models.CharField(max_length=100, blank=True, null=True)
    coupon = models.ForeignKey(
        'core.Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'
    
    def __str__(self):
        if self.user:
            return f"Cart - {self.user.email}"
        return f"Cart - {self.session_id}"
    
    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def discount_amount(self):
        if self.coupon and self.coupon.is_valid():
            if self.coupon.discount_type == 'percentage':
                return (self.subtotal * self.coupon.discount_value) / 100
            else:
                return min(self.coupon.discount_value, self.subtotal)
        return 0
    
    @property
    def shipping_cost(self):
        if self.subtotal >= settings.FREE_SHIPPING_THRESHOLD:
            return 0
        return settings.SHIPPING_FEE
    
    @property
    def total(self):
        return self.subtotal - self.discount_amount + self.shipping_cost
    
    def apply_coupon(self, coupon_code):
        """Apply a coupon to the cart."""
        from chris_lux.core.models import Coupon
        try:
            coupon = Coupon.objects.get(code=coupon_code.upper(), is_active=True)
            if coupon.is_valid():
                if self.subtotal >= coupon.minimum_order:
                    self.coupon = coupon
                    self.save()
                    return True, f"Coupon '{coupon.code}' applied successfully!"
                else:
                    return False, f"Minimum order amount of ₦{coupon.minimum_order} required."
            else:
                return False, "This coupon has expired or reached its usage limit."
        except Coupon.DoesNotExist:
            return False, "Invalid coupon code."
    
    def remove_coupon(self):
        """Remove coupon from cart."""
        self.coupon = None
        self.save()


class CartItem(models.Model):
    """Cart item model."""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation = models.ForeignKey(
        Variation,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        unique_together = ['cart', 'product', 'variation']
        ordering = ['-added_at']
    
    def __str__(self):
        if self.variation:
            return f"{self.quantity}x {self.product.name} ({self.variation.value})"
        return f"{self.quantity}x {self.product.name}"
    
    @property
    def unit_price(self):
        if self.variation:
            return self.variation.final_price
        return self.product.price
    
    @property
    def subtotal(self):
        return self.unit_price * self.quantity
