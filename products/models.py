from django.db import models
from category.models import Category
from userauths.models import User
from django.utils.text import slugify
from django.db.models import Avg, Count
from PIL import Image
import imghdr
import os
from django.conf import settings
from django.core.exceptions import ValidationError

class Brand(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


import base64
from django.core.files.base import ContentFile


def product_image_upload_path(instance, filename):
    """Defines the dynamic upload path for product images."""
    return f'product_images/{instance.product.slug}/{filename}'


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey('category.Category', on_delete=models.CASCADE, related_name="products")
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE, related_name="products")
    description = models.TextField()
    highlights = models.TextField(help_text="Enter specifications as bullet points", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Removed price, discount_price, stock and has_variants

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_default_variant(self):
        """Returns the default variant; if none is explicitly marked, returns the first available variant."""
        default_variant = self.variants.filter(is_default=True).first()
        return default_variant if default_variant else self.variants.first()

    def get_final_price(self):
        """
        Returns the final price based on the default variant.
        If a discount is set (greater than 0), that value is used.
        """
        default_variant = self.get_default_variant()
        if default_variant:
            return default_variant.discount if default_variant.discount > 0 else default_variant.price
        return 0

    def average_rating(self):
        return self.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0.0

    def review_count(self):
        return self.reviews.aggregate(count=Count('id'))['count'] or 0

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    variant_name = models.CharField(max_length=100, help_text="e.g., Size, Color")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)  # Will be set by IMS/POS
    is_default = models.BooleanField(default=False, help_text="Set as default variant for display.")

    def __str__(self):
        return f"{self.product.name} - {self.variant_name}"
    
    @property
    def final_price(self):
        """
        If discount is set (greater than 0), it is treated as the final selling price.
        Otherwise, the original price is used.
        """
        return self.discount if self.discount > 0 else self.price
    
    @property
    def discount_percentage(self):
        """Calculate the discount percentage"""
        if self.discount > 0 and self.price > 0:
            return round(((self.price - self.discount) / self.price) * 100, 2)
        return 0

    def save(self, *args, **kwargs):
        # If this variant is marked as default, unset the default flag on all other variants for this product.
        if self.is_default:
            ProductVariant.objects.filter(product=self.product, is_default=True).exclude(pk=self.pk).update(is_default=False)
        else:
            # Auto-set as default if no default exists.
            if not ProductVariant.objects.filter(product=self.product, is_default=True).exists():
                self.is_default = True
        super().save(*args, **kwargs)


class ProductImage(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=product_image_upload_path)

    def __str__(self):
        return f"{self.product.name} - Image"
    
    @staticmethod
    def validate_image(image_data, product):
        """
        Validates base64 image data for format (PNG/JPEG) and size (max 5MB).
        Returns the decoded image file if valid, otherwise raises ValidationError.
        """
        try:
            # Expecting data in the format: "data:image/jpeg;base64,/9j/..."
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1].lower()
            
            # Validate format
            if ext not in ['png', 'jpeg']:
                raise ValidationError(f"Invalid image format: {ext}. Only PNG and JPEG are allowed.")

            # Decode base64 data
            image_bytes = base64.b64decode(imgstr)
            
            # Validate image type using imghdr
            image_type = imghdr.what(None, h=image_bytes)
            if image_type not in ['png', 'jpeg']:
                raise ValidationError(f"Invalid image content: detected {image_type or 'unknown'}. Only PNG and JPEG are allowed.")

            # Validate size (5MB = 5 * 1024 * 1024 bytes)
            max_size = 5 * 1024 * 1024
            if len(image_bytes) > max_size:
                raise ValidationError(f"Image size exceeds 5MB (size: {len(image_bytes) / (1024 * 1024):.2f}MB).")

            # Create ContentFile
            image_file = ContentFile(image_bytes, name=f"{product.slug}.{ext}")
            return image_file
        except Exception as e:
            raise ValidationError(f"Error processing image: {str(e)}")

    @staticmethod
    def save_cropped_image(image_data, product):
        """
        Decodes a base64 image string and creates a ProductImage after validation.
        Raises ValidationError if validation fails.
        """
        image_file = ProductImage.validate_image(image_data, product)
        return ProductImage.objects.create(product=product, image=image_file)


class Review(models.Model):
    product = models.ForeignKey(Product, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"

