from django.db import models
from django.utils.text import slugify
from .validators import validate_no_leading_trailing_spaces, validate_image_size, validate_category_name, validate_image_format # Import validators

class Category(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        validators=[validate_no_leading_trailing_spaces, validate_category_name],  # Apply validation
    )
    description = models.TextField(blank=False, default="no description")
    image = models.ImageField(
        upload_to='category_images/',
        blank=False,
        null=False,
        validators=[validate_image_size,validate_image_format]  # Apply image validation
    )
    slug = models.SlugField(max_length=255, unique=True)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, blank=True, null=True, related_name='subcategories'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)  # Auto-generate slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'
