
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
import json

from .models import Product, ProductImage, Brand, ProductVariant ,Review
from category.models import Category
from userauths.decorators import role_required
from django.db.models import Avg
from django.core.exceptions import ValidationError

# ---------------------------
# Admin: Product Management
# ---------------------------

#temp

@role_required(allowed_roles=['admin'])
def perm_delete_product(request, pk):
    product = get_object_or_404(Product, id=pk)
    # Delete all associated images
    for image in product.images.all():
        image.image.delete()  # delete the image file from storage
        image.delete()        # delete the image record from DB
    product.delete()  # delete the product itself
    messages.success(request, "Product deleted successfully.")
    return redirect('products:admin_product_list')



# Admin: Add Product

# @role_required(allowed_roles=['admin'])
# def add_product(request):
#     if request.method == 'POST':
#         # Process product fields
#         name = request.POST.get('name', '').strip()
#         slug = request.POST.get('slug', '').strip() or None
#         category_id = request.POST.get('category')
#         brand_id = request.POST.get('brand')
#         description = request.POST.get('description', '').strip()
#         highlights = request.POST.get('highlights', '').strip()
#         is_active = request.POST.get('is_active') == 'on'

#         # Validate required product fields
#         if not name:
#             messages.error(request, "Product name cannot be empty.")
#             return render(request, 'products/add_product.html', {
#                 'categories': Category.objects.all(),
#                 'brands': Brand.objects.all(),
#                 'form_data': request.POST,
#             })


#         if Product.objects.filter(slug=slug).exists():
#             messages.error(request, "Slug name already exists.")
#             return render(request, 'products/add_product.html', {
#                 'categories': Category.objects.all(),
#                 'brands': Brand.objects.all(),
#                 'form_data': request.POST,
#             })
        
#         if not Category.objects.filter(id=category_id).exists():
#             messages.error(request, "Selected category is invalid.")
#             return render(request, 'products/add_product.html', {
#                 'categories': Category.objects.all(),
#                 'brands': Brand.objects.all(),
#                 'form_data': request.POST,
#             })

#         if not Brand.objects.filter(id=brand_id).exists():
#             messages.error(request, "Selected brand is invalid.")
#             return render(request, 'products/add_product.html', {
#                 'categories': Category.objects.all(),
#                 'brands': Brand.objects.all(),
#                 'form_data': request.POST,
#             })

#         if not description:
#             messages.error(request, "Product description cannot be empty.")
#             return render(request, 'products/add_product.html', {
#                 'categories': Category.objects.all(),
#                 'brands': Brand.objects.all(),
#                 'form_data': request.POST,
#             })

#         # Create the product (without price/discount/stock)
#         product = Product.objects.create(
#             name=name,
#             slug=slug,
#             category_id=category_id,
#             brand_id=brand_id,
#             description=description,
#             highlights=highlights,
#             is_active=is_active
#         )

#         # Process Variants (at least one variant is required)
#         variant_names = request.POST.getlist('variant_name[]')
#         variant_prices = request.POST.getlist('variant_price[]')
#         variant_discounts = request.POST.getlist('variant_discount[]')
#         variant_stocks = request.POST.getlist('variant_stock[]')
#         variant_defaults = request.POST.getlist('variant_default[]')  # Checkbox values; expect 'on' if checked

#         if not variant_names or not any(name.strip() for name in variant_names):
#             messages.error(request, "At least one variant must be provided.")
#             product.delete()  # Clean up the created product
#             return render(request, 'products/add_product.html', {
#                 'categories': Category.objects.all(),
#                 'brands': Brand.objects.all(),
#                 'form_data': request.POST,
#             })

#         # Track variant names to ensure uniqueness
#         seen_variant_names = set()
#         valid_variants = False

#         for idx, v_name in enumerate(variant_names):
#             v_name = v_name.strip()
#             if not v_name:
#                 messages.error(request, "Variant name cannot be empty.")
#                 continue

#             # Check for duplicate variant names within the form submission
#             if v_name.lower() in seen_variant_names:
#                 messages.error(request, f"Variant name '{v_name}' is duplicated in the form.")
#                 continue
#             seen_variant_names.add(v_name.lower())

#             try:
#                 v_price = float(variant_prices[idx])
#                 v_discount = float(variant_discounts[idx]) if variant_discounts[idx].strip() else 0.0
#                 v_stock = int(variant_stocks[idx]) if variant_stocks[idx].strip() else 0
#             except (ValueError, IndexError):
#                 messages.error(request, f"Invalid values for price, discount, or stock for variant '{v_name}'.")
#                 continue

#             # Validate variant values
#             if v_price <= 0:
#                 messages.error(request, f"Price for variant '{v_name}' must be a positive number.")
#                 continue
#             if v_discount >= v_price:
#                 messages.error(request, f"Discount for variant '{v_name}' cannot exceed or equal its price.")
#                 continue
#             if v_stock < 0:
#                 messages.error(request, f"Stock for variant '{v_name}' cannot be negative.")
#                 continue
#             if v_discount < 0:
#                 messages.error(request, f"Discount for variant '{v_name}' must be positive.")
#                 continue

#             is_default = False
#             try:
#                 if variant_defaults[idx] == 'on':
#                     is_default = True
#             except IndexError:
#                 is_default = False

#             # Create the variant
#             ProductVariant.objects.create(
#                 product=product,
#                 variant_name=v_name,
#                 price=v_price,
#                 discount=v_discount,
#                 stock=v_stock,
#                 is_default=is_default
#             )
#             valid_variants = True

#         if not valid_variants:
#             messages.error(request, "No valid variants were provided.")
#             product.delete()  # Clean up the created product
#             return render(request, 'products/add_product.html', {
#                 'categories': Category.objects.all(),
#                 'brands': Brand.objects.all(),
#                 'form_data': request.POST,
#             })

#         # Process and save cropped images
#         # cropped_images_json = request.POST.get('cropped_images', '[]')
#         # try:
#         #     cropped_images = json.loads(cropped_images_json)
#         #     for image_dict in cropped_images:
#         #         image_base64 = image_dict.get('image')
#         #         if image_base64:
#         #             ProductImage.save_cropped_image(image_base64, product)
#         # except json.JSONDecodeError:
#         #     messages.error(request, "Invalid cropped images data.")
#         #     product.delete()  # Clean up the created product
#         #     return render(request, 'products/add_product.html', {
#         #         'categories': Category.objects.all(),
#         #         'brands': Brand.objects.all(),
#         #         'form_data': request.POST,
#         #     })

#         # messages.success(request, "Product and variants added successfully!")
#         # return redirect('products:admin_product_list')

#         # Process and save cropped images
#         cropped_images_json = request.POST.get('cropped_images', '[]')
#         try:
#             cropped_images = json.loads(cropped_images_json)
#             if not cropped_images:
#                 messages.error(request, "At least one image is required.")
#                 product.delete()
#                 return render(request, 'products/add_product.html', {
#                     'categories': Category.objects.all(),
#                     'brands': Brand.objects.all(),
#                     'form_data': request.POST,
#                 })

#             valid_images = False
#             for image_dict in cropped_images:
#                 image_base64 = image_dict.get('image')
#                 if image_base64:
#                     image_instance, error = ProductImage.save_cropped_image(image_base64, product)
#                     if error:
#                         messages.error(request, error)
#                         continue
#                     valid_images = True

#             if not valid_images:
#                 messages.error(request, "No valid images were provided. At least one valid PNG or JPEG image under 5MB is required.")
#                 product.delete()
#                 return render(request, 'products/add_product.html', {
#                     'categories': Category.objects.all(),
#                     'brands': Brand.objects.all(),
#                     'form_data': request.POST,
#                 })

#         except json.JSONDecodeError:
#             messages.error(request, "Invalid cropped images data.")
#             product.delete()
#             return render(request, 'products/add_product.html', {
#                 'categories': Category.objects.all(),
#                 'brands': Brand.objects.all(),
#                 'form_data': request.POST,
#             })

#         messages.success(request, "Product and variants added successfully!")
#         return redirect('products:admin_product_list')
#     else:
#         categories = Category.objects.all()
#         brands = Brand.objects.all()
#         return render(request, 'products/add_product.html', {
#             'categories': categories,
#             'brands': brands,
#             'form_data': {},  # Empty form data for GET request
#         })


import json
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from .models import Product, ProductVariant, ProductImage, Category, Brand
from .validators import validate_base64_image

@role_required(allowed_roles=['admin'])
def add_product(request):
    if request.method == "POST":
        errors = []

        # Product Fields
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip() or None
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')
        description = request.POST.get('description', '').strip()
        highlights = request.POST.get('highlights', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        # Validate Product Fields
        if not name:
            errors.append("Product name is required.")
        elif len(name) > 255:
            errors.append("Product name should not exceed 255 characters.")

        if not Category.objects.filter(id=category_id).exists():
            errors.append("Selected category is invalid.")

        if not Brand.objects.filter(id=brand_id).exists():
            errors.append("Selected brand is invalid.")

        if not description:
            errors.append("Description is required.")
        elif len(description) < 10:
            errors.append("Description must be at least 10 characters long.")

        if slug and Product.objects.filter(slug__iexact=slug).exists():
            errors.append("Slug already exists.")

        # Validate Variants
        variant_names = request.POST.getlist('variant_name[]')
        variant_prices = request.POST.getlist('variant_price[]')
        variant_discounts = request.POST.getlist('variant_discount[]')
        variant_stocks = request.POST.getlist('variant_stock[]')
        variant_defaults = request.POST.getlist('variant_default[]')

        if not variant_names or not any(name.strip() for name in variant_names):
            errors.append("At least one variant is required.")

        seen_variant_names = set()
        valid_variants = []

        for idx, v_name in enumerate(variant_names):
            v_name = v_name.strip()
            if not v_name:
                errors.append("Variant name cannot be empty.")
                continue

            if v_name.lower() in seen_variant_names:
                errors.append(f"Variant name '{v_name}' is duplicated.")
                continue
            seen_variant_names.add(v_name.lower())

            try:
                v_price = float(variant_prices[idx])
                v_discount = float(variant_discounts[idx]) if variant_discounts[idx].strip() else 0.0
                v_stock = int(variant_stocks[idx]) if variant_stocks[idx].strip() else 0
            except (ValueError, IndexError):
                errors.append(f"Invalid values for price, discount, or stock for variant '{v_name}'.")
                continue

            if v_price <= 0:
                errors.append(f"Price for variant '{v_name}' must be positive.")
                continue
            if v_discount >= v_price:
                errors.append(f"Discount for variant '{v_name}' cannot exceed or equal its price.")
                continue
            if v_stock < 0:
                errors.append(f"Stock for variant '{v_name}' cannot be negative.")
                continue
            if v_discount < 0:
                errors.append(f"Discount for variant '{v_name}' must be positive.")
                continue

            is_default = variant_defaults[idx] == 'on' if idx < len(variant_defaults) else False
            valid_variants.append({
                'name': v_name,
                'price': v_price,
                'discount': v_discount,
                'stock': v_stock,
                'is_default': is_default
            })

        if not valid_variants:
            errors.append("No valid variants provided.")

        # Validate Images
        cropped_images_json = request.POST.get('cropped_images', '[]')
        try:
            cropped_images = json.loads(cropped_images_json)
        except json.JSONDecodeError:
            errors.append("Invalid image data format. Please upload valid images.")

        if not cropped_images:
            errors.append("At least one image is required.")

        valid_images = []
        if cropped_images and not errors:
            for image_dict in cropped_images:
                image_base64 = image_dict.get('image')
                if not image_base64:
                    errors.append("Missing image data.")
                    continue
                try:
                    # Validate image, store base64 if valid
                    validate_base64_image(image_base64, slug or 'temp')
                    valid_images.append(image_base64)
                except ValidationError as e:
                    errors.extend(e.messages)

        if not valid_images:
            errors.append("No valid images provided. Images must be PNG/JPEG and under 5MB.")

        # Display Errors
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'products/add_product.html', {
                'categories': Category.objects.all(),
                'brands': Brand.objects.all(),
                'form_data': request.POST,
            })

        # Save Product
        product = Product.objects.create(
            name=name,
            slug=slug,
            category_id=category_id,
            brand_id=brand_id,
            description=description,
            highlights=highlights,
            is_active=is_active
        )

        # Save Variants
        for variant in valid_variants:
            ProductVariant.objects.create(
                product=product,
                variant_name=variant['name'],
                price=variant['price'],
                discount=variant['discount'],
                stock=variant['stock'],
                is_default=variant['is_default']
            )

        # Save Images
        for image_base64 in valid_images:
            ProductImage.save_cropped_image(image_base64, product)

        messages.success(request, "Product added successfully!")
        return redirect('products:admin_product_list')

    categories = Category.objects.all()
    brands = Brand.objects.all()
    return render(request, 'products/add_product.html', {
        'categories': categories,
        'brands': brands,
        'form_data': {},
    })

import json
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from .models import Product, ProductVariant, ProductImage, Category, Brand
from .validators import validate_base64_image

@role_required(allowed_roles=['admin'])
def edit_product(request, product_id):
    product = get_object_or_404(Product.objects.prefetch_related('images', 'variants'), id=product_id)

    if request.method == "POST":
        errors = []

        # Product Fields
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip() or None
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')
        description = request.POST.get('description', '').strip()
        highlights = request.POST.get('highlights', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        # Validate Product Fields
        if not name:
            errors.append("Product name is required.")
        elif len(name) > 255:
            errors.append("Product name should not exceed 255 characters.")

        if not Category.objects.filter(id=category_id).exists():
            errors.append("Selected category is invalid.")

        if not Brand.objects.filter(id=brand_id).exists():
            errors.append("Selected brand is invalid.")

        if not description:
            errors.append("Description is required.")
        elif len(description) < 10:
            errors.append("Description must be at least 10 characters long.")

        if slug and Product.objects.filter(slug__iexact=slug).exclude(id=product_id).exists():
            errors.append("Slug already exists.")

        # Validate New Variants
        new_variant_names = request.POST.getlist('new_variant_name[]')
        new_variant_prices = request.POST.getlist('new_variant_price[]')
        new_variant_discounts = request.POST.getlist('new_variant_discount[]')
        new_variant_stocks = request.POST.getlist('new_variant_stock[]')
        new_variant_defaults = request.POST.getlist('new_variant_default[]')

        seen_variant_names = {v.variant_name.lower() for v in product.variants.all()}
        valid_new_variants = []

        for idx, v_name in enumerate(new_variant_names):
            v_name = v_name.strip()
            if not v_name:
                continue  # Skip empty variants

            if v_name.lower() in seen_variant_names:
                errors.append(f"Variant name '{v_name}' is duplicated.")
                continue
            seen_variant_names.add(v_name.lower())

            try:
                v_price = float(new_variant_prices[idx])
                v_discount = float(new_variant_discounts[idx]) if new_variant_discounts[idx].strip() else 0.0
                v_stock = int(new_variant_stocks[idx]) if new_variant_stocks[idx].strip() else 0
            except (ValueError, IndexError):
                errors.append(f"Invalid values for price, discount, or stock for variant '{v_name}'.")
                continue

            if v_price <= 0:
                errors.append(f"Price for variant '{v_name}' must be positive.")
                continue
            if v_discount >= v_price:
                errors.append(f"Discount for variant '{v_name}' cannot exceed or equal its price.")
                continue
            if v_stock < 0:
                errors.append(f"Stock for variant '{v_name}' cannot be negative.")
                continue
            if v_discount < 0:
                errors.append(f"Discount for variant '{v_name}' must be positive.")
                continue

            is_default = False
            # If the corresponding checkbox exists and is "on"
            if idx < len(new_variant_defaults) and new_variant_defaults[idx] == "on":
                is_default = True
            valid_new_variants.append({
                'name': v_name,
                'price': v_price,
                'discount': v_discount,
                'stock': v_stock,
                'is_default': is_default
            })

        # Validate Images
        cropped_images_json = request.POST.get('cropped_images', '[]')
        try:
            cropped_images = json.loads(cropped_images_json)
        except json.JSONDecodeError:
            errors.append("Invalid image data format. Please upload valid images.")

        valid_images = []
        if cropped_images and not errors:
            for image_dict in cropped_images:
                image_base64 = image_dict.get('image')
                if not image_base64:
                    errors.append("Missing image data.")
                    continue
                try:
                    validate_base64_image(image_base64, slug or product.slug)
                    valid_images.append(image_base64)
                except ValidationError as e:
                    errors.extend(e.messages)

        # Handle Deleted Images
        deleted_images_json = request.POST.get('deleted_images', '[]')
        try:
            deleted_images = json.loads(deleted_images_json)
        except json.JSONDecodeError:
            errors.append("Invalid deleted images format.")
            deleted_images = []

        # Ensure at least one image remains
        remaining_images = product.images.exclude(id__in=deleted_images).count()
        if not valid_images and remaining_images == 0:
            errors.append("At least one image is required.")

        # Display Errors
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'products/edit_product.html', {
                'product': product,
                'categories': Category.objects.all(),
                'brands': Brand.objects.all(),
                'form_data': request.POST,
                'product_images': product.images.all(),
                'variants': product.variants.all()
            })

        # Update Product
        product.name = name
        product.slug = slug
        product.category_id = category_id
        product.brand_id = brand_id
        product.description = description
        product.highlights = highlights
        product.is_active = is_active
        product.save()

        # Save New Variants
        for variant in valid_new_variants:
            ProductVariant.objects.create(
                product=product,
                variant_name=variant['name'],
                price=variant['price'],
                discount=variant['discount'],
                stock=variant['stock'],
                is_default=variant['is_default']
            )

        # Delete Images
        if deleted_images:
            ProductImage.objects.filter(id__in=deleted_images, product=product).delete()

        # Save New Images
        for image_base64 in valid_images:
            ProductImage.save_cropped_image(image_base64, product)

        messages.success(request, "Product updated successfully!")
        return redirect('products:admin_product_list')

    categories = Category.objects.all()
    brands = Brand.objects.all()
    form_data = {
        'name': product.name,
        'slug': product.slug or '',
        'category': str(product.category_id),
        'brand': str(product.brand_id),
        'description': product.description,
        'highlights': product.highlights or '',
        'is_active': 'on' if product.is_active else '',
        'new_variant_name': [],
        'new_variant_price': [],
        'new_variant_discount': [],
        'new_variant_stock': [],
        'new_variant_default': []
    }
    return render(request, 'products/edit_product.html', {
        'product': product,
        'categories': categories,
        'brands': brands,
        'form_data': form_data,
        'product_images': product.images.all(),
        'variants': product.variants.all()
    })



from django.core.paginator import Paginator
from django.db.models import Q

@role_required(['admin'])
def product_list_admin(request):
    search_query = request.GET.get('search', '')
    
    products = Product.objects.all().order_by('-updated_at')

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(brand__name__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    paginator = Paginator(products, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "products/product_list.html", {
        "products": page_obj,
        "search_query": search_query
    })




# Admin: Delete Product Image

@role_required(allowed_roles=['admin'])
def delete_image(request, pk):
    image = get_object_or_404(ProductImage, pk=pk)
    product = image.product
    
    try:
        # If this is the main image, set another image as main if available
        if product.main_image == image:
            alternative_image = product.images.exclude(pk=pk).first()
            if alternative_image:
                product.main_image = alternative_image
                product.save()
        
        image.delete()
        messages.success(request, 'Image deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting image: {str(e)}')
    
    return redirect(request.META.get('HTTP_REFERER', 'products:edit_product', args=[product.id]))



@role_required(allowed_roles=['admin'])
def delete_product(request, pk):
    """Soft delete a product via AJAX"""
    product = get_object_or_404(Product, pk=pk)
    product.is_active = False
    product.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'deleted', 'product_id': pk})

    messages.success(request, "Product successfully deleted!")
    return redirect("products:admin_product_list")


@role_required(allowed_roles=['admin'])
def restore_product(request, pk):
    """Restore a soft-deleted product via AJAX"""
    product = get_object_or_404(Product, pk=pk, is_active=False)
    product.is_active=True
    product.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'restored', 'product_id': pk})

    messages.success(request, "Product successfully restored!")
    return redirect("products:admin_product_list")


# ---------------------------
# Variant Management Views
# ---------------------------

# @role_required(allowed_roles=['admin'])
# def add_variant(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     if request.method == "POST":
#         variant_name = request.POST.get("variant_name", "").strip()
#         price = request.POST.get("price")
#         discount = request.POST.get("discount", "0")
#         stock = request.POST.get("stock")
#         is_default = request.POST.get("is_default") == "on"

#         # Prepare form data to repopulate the template on error
#         form_data = {
#             "variant_name": variant_name,
#             "price": price,
#             "discount": discount,
#             "stock": stock,
#             "is_default": is_default,
#         }

#         # Validation checks
#         if not variant_name:
#             messages.error(request, "Variant name cannot be empty.")
#             return render(request, "products/edit_product.html", {"product": product, "add_variant_form_data": form_data})

#         if ProductVariant.objects.filter(product__id=product.id, variant_name__iexact=variant_name).exists():
#             messages.error(request, "Variant name already exists for this product.")
#             return render(request, "products/edit_product.html", {"product": product, "add_variant_form_data": form_data})

#         try:
#             price = float(price)
#             discount = float(discount)
#             stock = int(stock)
#             if price <= 0:
#                 messages.error(request, "Price must be positive.")
#                 return render(request, "products/edit_product.html", {"product": product, "add_variant_form_data": form_data})
#             if discount >= price:
#                 messages.error(request, "Discount cannot exceed or equal to price.")
#                 return render(request, "products/edit_product.html", {"product": product, "add_variant_form_data": form_data})
#             if stock < 0:
#                 messages.error(request, "Stock cannot be negative.")
#                 return render(request, "products/edit_product.html", {"product": product, "add_variant_form_data": form_data})
#             if discount < 0:
#                 messages.error(request, "Discount must be positive.")
#                 return render(request, "products/edit_product.html", {"product": product, "add_variant_form_data": form_data})
#         except ValueError:
#             messages.error(request, "Invalid values for price, discount, or stock.")
#             return render(request, "products/edit_product.html", {"product": product, "add_variant_form_data": form_data})

#         # If all validations pass, create the variant
#         ProductVariant.objects.create(
#             product=product,
#             variant_name=variant_name,
#             price=price,
#             discount=discount,
#             stock=stock,
#             is_default=is_default
#         )
#         messages.success(request, "Variant added successfully.")
#         return redirect("products:edit_product", product_id=product.id)

#     # For GET request, provide empty form data
#     form_data = {
#         "variant_name": "",
#         "price": "",
#         "discount": "0",
#         "stock": "",
#         "is_default": False,
#     }
#     return render(request, "products/edit_product.html", {"product": product, "add_variant_form_data": form_data})


@role_required(allowed_roles=['admin'])
def edit_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    if request.method == "POST":
        variant_name = request.POST.get("variant_name", "").strip()
        price = request.POST.get("price")
        discount = request.POST.get("discount", "0")
        stock = request.POST.get("stock")
        is_default = request.POST.get("is_default") == "on"

        # Prepare form data to repopulate the template on error
        form_data = {
            "variant_name": variant_name,
            "price": price,
            "discount": discount,
            "stock": stock,
            "is_default": is_default,
        }

        # Validation checks
        if not variant_name:
            messages.error(request, "Variant name cannot be empty.")
            return render(request, "products/edit_variant.html", {"variant": variant, "form_data": form_data})

        if ProductVariant.objects.filter(product__id=variant.product.id, variant_name__iexact=variant_name).exclude(id=variant.id).exists():
            messages.error(request, "Variant name already exists for this product.")
            return render(request, "products/edit_variant.html", {"variant": variant, "form_data": form_data})

        try:
            price = float(price)
            discount = float(discount)
            stock = int(stock)
            if price <= 0:
                messages.error(request, "Price must be positive.")
                return render(request, "products/edit_variant.html", {"variant": variant, "form_data": form_data})
            if discount >= price:
                messages.error(request, "Discount cannot exceed or equal to price.")
                return render(request, "products/edit_variant.html", {"variant": variant, "form_data": form_data})
            if stock <= 0:
                messages.error(request, "Stock should be positive.")
                return render(request, "products/edit_variant.html", {"variant": variant, "form_data": form_data})
            if discount < 0:
                messages.error(request, "Discount must be positive.")
                return render(request, "products/edit_variant.html", {"variant": variant, "form_data": form_data})
        except ValueError:
            messages.error(request, "Invalid values for price, discount, or stock.")
            return render(request, "products/edit_variant.html", {"variant": variant, "form_data": form_data})

        # If all validations pass, save the variant
        variant.variant_name = variant_name
        variant.price = price
        variant.discount = discount
        variant.stock = stock
        variant.is_default = is_default
        variant.save()
        messages.success(request, "Variant updated successfully.")
        return redirect("products:edit_product", product_id=variant.product.id)

    # For GET request, populate form with existing variant data
    form_data = {
        "variant_name": variant.variant_name,
        "price": variant.price,
        "discount": variant.discount,
        "stock": variant.stock,
        "is_default": variant.is_default,
    }
    return render(request, "products/edit_variant.html", {"variant": variant, "form_data": form_data})


@role_required(allowed_roles=['admin'])
def delete_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    product_id = variant.product.id
    variant.delete()
    messages.success(request, "Variant deleted successfully.")
    return redirect("products:edit_product", product_id=product_id)


# ---------------------------
# User Views
# ---------------------------

# User: Product Detail

def product_detail(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand')
        .prefetch_related('images', 'reviews', 'variants'),
        pk=product_id, 
        is_active=True
    )
    reviews = product.reviews.all().order_by("-created_at")
    avg_rating = reviews.aggregate_avg = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    related_products = Product.objects.filter(is_active=True).exclude(pk=product_id)[:4]

    # Use first image as detail image; fall back to a placeholder.
    first_image = product.images.first()
    product.detail_image = first_image.image.url if first_image else "/static/images/placeholder.jpg"

    # Get the default variant using the helper method from the model.
    default_variant = product.get_default_variant()
    
    # Use the model's method to get the effective selling price.
    effective_price = product.get_final_price()

    # Pass all variants so the template can update prices when a variant is selected.
    variants = product.variants.all()

    return render(request, "products/product_detail.html", {
        "product": product,
        "reviews": reviews,
        "avg_rating": avg_rating,
        "related_products": related_products,
        "default_variant": default_variant,
        "effective_price": effective_price,
        "variants": variants,
    })


# User: Product List

def shop_list(request):
    
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.prefetch_related("images", "variants").filter(is_active=True, category__is_active=True)
    reviews = Review.objects.all()
    # Filtering by category
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    # Filtering by price range using the default variant's price
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(variants__is_default=True, variants__price__gte=min_price).distinct()
    if max_price:
        products = products.filter(variants__is_default=True, variants__price__lte=max_price).distinct()

    # Sorting (using the default variant's price)
    sort_by = request.GET.get('sort_by')
    if sort_by == 'price_low_high':
        products = products.order_by('variants__price')
    elif sort_by == 'price_high_low':
        products = products.order_by('-variants__price')
    elif sort_by == 'rating':
        products = products.order_by('reviews__rating')
    else:
        products = products.order_by('id')

    # Pagination (6 products per page)
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    paged_products = paginator.get_page(page_number)

    # Assign a thumbnail from the product images
    for product in paged_products:
        first_image = product.images.first()
        product.thumbnail = first_image.image if first_image else None

    context = {
        'products': paged_products,
        'categories': categories,
    }
    return render(request, 'products/shop_list.html', context)



# User: Add Review

from django.db.models import Q
from django.contrib import messages
from orders.models import *

@role_required(['customer'])
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Check if the user has purchased and received/returned the product
    eligible_orders = OrderSub.objects.filter(
        user=request.user,
        variant__product=product
    ).filter(
        Q(main_order__order_status="Delivered") | Q(status="Returned")
    )

    if not eligible_orders.exists():
        messages.error(request, "You can only review products you've purchased and received or returned.")
        return redirect("products:product_detail", product_id=product.id)

    if request.method == "POST":
        try:
            rating = int(request.POST.get("rating"))
        except (TypeError, ValueError):
            messages.error(request, "Invalid rating value.")
            return redirect("products:product_detail", product_id=product.id)

        comment = request.POST.get("comment", "").strip()

        if rating < 1 or rating > 5:
            messages.error(request, "Rating must be between 1 and 5.")
            return redirect("products:product_detail", product_id=product.id)

        # Check if user has already reviewed this product
        existing_review = Review.objects.filter(user=request.user, product=product).first()
        if existing_review:
            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.save()
        else:
            Review.objects.create(product=product, user=request.user, rating=rating, comment=comment)

        messages.success(request, "Your review has been submitted.")
        
    return redirect("products:product_detail", product_id=product.id)
