from django.db import models
from django.conf import settings
from products.models import Product, ProductVariant
from decimal import Decimal


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carts')
    coupon_code = models.CharField(max_length=50, blank=True, null=True)  # New field for coupon code
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    # Constants for shipping calculations
    FREE_SHIPPING_THRESHOLD = Decimal('1000.00')
    SHIPPING_COST = Decimal('50.00')

    def __str__(self):
        return f"Cart #{self.id} for {self.user}"

    def get_subtotal(self):
        """Calculate the subtotal for all active items in the cart using the final unit prices."""
        return sum(item.get_total_price() for item in self.items.filter(is_active=True))

    def get_shipping_cost(self):
        """Return shipping cost based on the subtotal."""
        if self.get_subtotal() >= self.FREE_SHIPPING_THRESHOLD:
            return Decimal('0.00')
        return self.SHIPPING_COST

    def get_discount(self):
        """Calculate a discount based on the coupon code. Example: SAVE10 gives 10% off."""
        if self.coupon_code == "SAVE10":
            return self.get_subtotal() * Decimal('0.10')
        return Decimal('0.00')

    def get_total(self):
        """Return the final total after applying shipping cost and any discount."""
        return self.get_subtotal() + self.get_shipping_cost()

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, default=None)
    quantity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True) 
    
    def __str__(self):
        return f"{self.quantity} x {self.variant}"
    
    def get_unit_price(self):
        """
        Return the final unit price for the variant.
        If a discount is applied (discount > 0), use the final_price,
        otherwise, use the regular price.
        """
        if self.variant.discount > 0:
            return self.variant.final_price
        return self.variant.price

    def total_cost(self):
        """Return total cost for this cart item (price * quantity)."""
        return self.variant.price * self.quantity

    def get_total_price(self):
        """Return total price for this cart item (price * quantity)."""
        return self.variant.discount * self.quantity if self.variant.discount > 0 else self.variant.price * self.quantity