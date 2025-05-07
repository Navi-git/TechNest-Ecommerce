from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from products.models import ProductImage

def process_and_save_image(product, uploaded_file):
    """Processes an uploaded image into three sizes (thumbnail, detail, zoom) and saves them in the database."""
    try:
        image = Image.open(uploaded_file)
    except Exception as e:
        print("Error opening image:", e)
        return

    # Define the sizes for each variant
    sizes = {
        'thumbnail': (250, 250),
        'detail': (600, 600),
        'zoom': (1200, 1200),
    }
    # Loop over each variant type and create a new record.
    for variant, dimensions in sizes.items():
        # Make a copy of the original image and resize it.
        img_copy = image.copy()
        img_copy.thumbnail(dimensions)  # Resize the image

        # Save the processed image to an in-memory buffer
        buffer = BytesIO()
        img_copy.save(buffer, format='JPEG', quality=90)
        buffer.seek(0)  # Move to the beginning of the buffer

        # Create a ContentFile with a modified filename
        variant_filename = f"{variant}_{uploaded_file.name}"
        image_file = ContentFile(buffer.read(), name=variant_filename)

        # Save the image variant to the database
        ProductImage.objects.create(
            product=product,
            image=image_file,
            variant=variant
        )
