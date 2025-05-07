from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

# Ensure name contains only letters, numbers, and spaces
validate_category_name = RegexValidator(
    regex=r'^[A-Za-z0-9 ]+$',
    message="Only letters, numbers, and spaces are allowed."
)

# Prevent leading/trailing spaces
def validate_no_leading_trailing_spaces(value):
    if value.strip() != value:
        raise ValidationError("Field should not have leading or trailing spaces.")

# Restrict image size to 2MB
def validate_image_size(image):
    max_size = 2 * 1024 * 1024  # 2MB
    if image.size > max_size:
        raise ValidationError("Image file size should not exceed 2MB.")
