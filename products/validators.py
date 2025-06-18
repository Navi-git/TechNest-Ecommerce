# products/validators.py
import base64
import imghdr
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

def validate_base64_image(image_data, slug):
    """
    Validates base64 image data for format (PNG/JPEG) and size (max 5MB).
    Returns ContentFile if valid, raises ValidationError if invalid.
    """
    try:
        # Expecting "data:image/jpeg;base64,/9j/..."
        format, imgstr = image_data.split(';base64,')
        ext = format.split('/')[-1].lower()

        if ext not in ['png', 'jpeg']:
            raise ValidationError(f"Invalid image format: {ext}. Only PNG and JPEG are allowed.")

        image_bytes = base64.b64decode(imgstr)
        image_type = imghdr.what(None, h=image_bytes)
        if image_type not in ['png', 'jpeg']:
            raise ValidationError(f"Invalid image content: detected {image_type or 'unknown'}.")

        max_size = 5 * 1024 * 1024  # 5MB
        if len(image_bytes) > max_size:
            raise ValidationError(f"Image size exceeds 5MB (size: {len(image_bytes) / (1024 * 1024):.2f}MB).")

        return ContentFile(image_bytes, name=f"{slug or 'temp'}.{ext}")
    except ValueError:
        raise ValidationError("Invalid base64 image data.")
    except Exception as e:
        raise ValidationError(f"Error processing image: {str(e)}")