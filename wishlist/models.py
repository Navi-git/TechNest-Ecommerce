from django.db import models
from userauths.models import *
from products.models import *

# Create your models here.

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'variant')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.variant.product.name} ({self.variant.variant_name})"