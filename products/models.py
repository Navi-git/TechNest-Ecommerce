from django.db import models
from category.models import Category
from userauths.models import User
from django.utils.text import slugify
from django.db.models import Avg, Count
from decimal import Decimal
from django.utils import timezone
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
        Returns the final price of the default variant (considering category & variant discounts).
        """
        default_variant = self.get_default_variant()
        if default_variant:
            return default_variant.final_price
        return Decimal('0.00')

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
        Returns the better of:
        - Variant-level discount
        - Category-level offer (if active)
        """
        base_price = self.price

        # Variant discount price
        variant_price = self.discount if self.discount > 0 else base_price

        # Category offer price
        category_offer = getattr(self.product.category, 'offer', None)
        if category_offer and category_offer.start_date <= timezone.now().date() <= category_offer.end_date:
            category_discount = Decimal(category_offer.discount_percentage)
            category_price = base_price * (Decimal('1.0') - (category_discount / Decimal('100')))
            return min(variant_price, category_price)

        return variant_price
    
    @property
    def discount_percentage(self):
        """
        Returns the actual discount percentage based on the best of:
        - variant discount
        - category offer (if active)
        """
        from decimal import Decimal
        from django.utils import timezone

        if self.price <= 0:
            return 0

        base_price = self.price

        # Variant discounted price
        variant_price = self.discount if self.discount > 0 else base_price

        # Category offer price
        category_offer = getattr(self.product.category, 'offer', None)
        if category_offer and category_offer.start_date <= timezone.now().date() <= category_offer.end_date:
            category_price = base_price * (Decimal('1.0') - (Decimal(category_offer.discount_percentage) / Decimal('100')))
            best_price = min(variant_price, category_price)
        else:
            best_price = variant_price

        discount_amount = base_price - best_price
        return round((discount_amount / base_price) * 100, 2)


    def save(self, *args, **kwargs):
        # If this variant is marked as default, unset the default flag on all other variants for this product.
        if self.is_default:
            ProductVariant.objects.filter(product=self.product, is_default=True).exclude(pk=self.pk).update(is_default=False)
        else:
            # Auto-set as default if no default exists.
            if not ProductVariant.objects.filter(product=self.product, is_default=True).exists():
                self.is_default = True
        super().save(*args, **kwargs)


# products/models.py
from django.db import models
from .validators import validate_base64_image

def product_image_upload_path(instance, filename):
    return f'product_images/{instance.product.slug}/{filename}'

# products/models.py
from django.db import models
from .validators import validate_base64_image

def product_image_upload_path(instance, filename):
    return f'product_images/{instance.product.slug}/{filename}'

class ProductImage(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=product_image_upload_path)

    def __str__(self):
        return f"{self.product.name} - Image"

    @staticmethod
    def save_cropped_image(image_data, product):
        """
        Validates and saves a base64 image string as a ProductImage.
        Returns ProductImage instance if successful, raises ValidationError if invalid.
        Assumes product is a saved instance.
        """
        if not product.pk:
            raise ValidationError("Product must be saved before saving images.")
        image_file = validate_base64_image(image_data, product.slug)
        return ProductImage.objects.create(product=product, image=image_file)

class Review(models.Model):
    product = models.ForeignKey(Product, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"

