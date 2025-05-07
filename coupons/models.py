from django.db import models
from django.conf import settings
from django.utils import timezone


# Create your models here.
class Coupon(models.Model):
    name = models.CharField(max_length=50,unique=True)
    code = models.CharField(max_length=15, unique=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, help_text="Discount amount or percentage")
    minimum_purchase = models.DecimalField(max_digits=10, decimal_places=2,default=0, 
        help_text="Minimum order amount required to apply coupon")
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2,default=0, 
        help_text="Maximum discount amount allowed for coupon")
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    status = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(default=1, 
        help_text="Total times this coupon can be used across users")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    """fuction to check if coupon is valid"""
    def is_valid(self):
        now = timezone.now()
        return self.status and self.valid_from <= now <= self.valid_to and self.usage_limit > 0
    
    """function to check if coupon is expired"""
    def is_expired(self):
        now = timezone.now()
        return now > self.valid_to
    

class CouponUser(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coupons')
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used = models.BooleanField(default=False)
    order_id = models.IntegerField(null=True, blank=True, 
        help_text="Reference to the Order ID where this coupon was used")
    redeemed_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'coupon')
        ordering = ['-redeemed_at']
    
    def __str__(self):
        return f"{self.user} for {self.coupon}"