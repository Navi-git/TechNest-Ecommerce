
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
import json

from .models import Product, ProductImage, Brand, ProductVariant ,Review
from category.models import Category
from userauths.decorators import role_required
from django.db.models import Avg


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

@role_required(allowed_roles=['admin'])
def add_product(request):
    if request.method == 'POST':
        # Process product fields
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip() or None
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')
        description = request.POST.get('description', '').strip()
        highlights = request.POST.get('highlights', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        # Validate required product fields
        if not name:
            messages.error(request, "Product name cannot be empty.")
            return redirect('products:add_product')

        if not Category.objects.filter(id=category_id).exists():
            messages.error(request, "Selected category is invalid.")
            return redirect('products:add_product')

        if not Brand.objects.filter(id=brand_id).exists():
            messages.error(request, "Selected brand is invalid.")
            return redirect('products:add_product')

        if not description:
            messages.error(request, "Product description cannot be empty.")
            return redirect('products:add_product')

        # Create the product (without price/discount/stock)
        product = Product.objects.create(
            name=name,
            slug=slug,
            category_id=category_id,
            brand_id=brand_id,
            description=description,
            highlights=highlights,
            is_active=is_active
        )

        # Process Variants (at least one variant is required)
        variant_names = request.POST.getlist('variant_name[]')
        variant_prices = request.POST.getlist('variant_price[]')
        variant_discounts = request.POST.getlist('variant_discount[]')
        variant_stocks = request.POST.getlist('variant_stock[]')
        variant_defaults = request.POST.getlist('variant_default[]')  # Checkbox values; expect 'on' if checked

        if not variant_names or not any(name.strip() for name in variant_names):
            messages.error(request, "At least one variant must be provided.")
            product.delete()  # Clean up the created product
            return redirect('products:add_product')

        for idx, v_name in enumerate(variant_names):
            if v_name.strip():
                try:
                    v_price = float(variant_prices[idx])
                    v_discount = float(variant_discounts[idx])
                    v_stock = int(variant_stocks[idx])
                except (ValueError, IndexError):
                    # Skip variant if conversion fails
                    continue

                # Validate variant values
                if v_price <= 0:
                    messages.error(request, "Variant price must be a positive number.")
                    continue
                if v_discount > v_price:
                    messages.error(request, "Variant discount cannot exceed its price.")
                    continue
                if v_stock < 0:
                    messages.error(request, "Variant stock cannot be negative.")
                    continue

                is_default = False
                try:
                    if variant_defaults[idx] == 'on':
                        is_default = True
                except IndexError:
                    is_default = False

                ProductVariant.objects.create(
                    product=product,
                    variant_name=v_name,
                    price=v_price,
                    discount=v_discount,
                    stock=v_stock,
                    is_default=is_default
                )

        # Process and save cropped images
        cropped_images_json = request.POST.get('cropped_images', '[]')
        try:
            cropped_images = json.loads(cropped_images_json)
            for image_dict in cropped_images:
                image_base64 = image_dict.get('image')
                if image_base64:
                    ProductImage.save_cropped_image(image_base64, product)
        except json.JSONDecodeError:
            messages.error(request, "Invalid cropped images data.")
            return redirect('products:add_product')

        messages.success(request, "Product added successfully!")
        return redirect('products:admin_product_list')

    else:
        categories = Category.objects.all()
        brands = Brand.objects.all()
        return render(request, 'products/add_product.html', {
            'categories': categories,
            'brands': brands
        })




@role_required(allowed_roles=['admin'])
def edit_product(request, product_id):
    product = get_object_or_404(Product.objects.prefetch_related('images', 'variants'), id=product_id)
    
    if request.method == 'POST':
        # Update product fields (price/stock now reside in variants)
        product.name = request.POST.get('name')
        product.slug = request.POST.get('slug') or None
        product.category_id = request.POST.get('category')
        product.brand_id = request.POST.get('brand')
        product.description = request.POST.get('description')
        product.highlights = request.POST.get('highlights')
        product.is_active = request.POST.get('is_active') == 'on'
        product.save()

        # Handle deleted images
        deleted_images_json = request.POST.get('deleted_images', '[]')
        try:
            deleted_images = json.loads(deleted_images_json)
        except json.JSONDecodeError:
            deleted_images = []

        if deleted_images:
            ProductImage.objects.filter(id__in=deleted_images).delete()

        # Process and save new cropped images
        cropped_images_json = request.POST.get('cropped_images', '[]')
        try:
            cropped_images = json.loads(cropped_images_json)
        except json.JSONDecodeError:
            cropped_images = []
        
        for image_dict in cropped_images:
            image_base64 = image_dict.get('image')
            if image_base64:
                ProductImage.save_cropped_image(image_base64, product)


        # After processing product update, images, etc.
        # Process new variant data
        new_variant_names = request.POST.getlist('new_variant_name[]')
        new_variant_prices = request.POST.getlist('new_variant_price[]')
        new_variant_discounts = request.POST.getlist('new_variant_discount[]')
        new_variant_stocks = request.POST.getlist('new_variant_stock[]')
        new_variant_defaults = request.POST.getlist('new_variant_default[]')  # checkbox values (e.g., "on")

        for idx, variant_name in enumerate(new_variant_names):
            if variant_name.strip():
                try:
                    price = float(new_variant_prices[idx])
                    discount = float(new_variant_discounts[idx])
                    stock = int(new_variant_stocks[idx])
                except (ValueError, IndexError):
                    # Skip this variant if conversion fails
                    continue

                is_default = False
                # If the corresponding checkbox exists and is "on"
                if idx < len(new_variant_defaults) and new_variant_defaults[idx] == "on":
                    is_default = True

                # Create the new variant associated with the product
                ProductVariant.objects.create(
                    product=product,
                    variant_name=variant_name,
                    price=price,
                    discount=discount,
                    stock=stock,
                    is_default=is_default
                )


        messages.success(request, "Product updated successfully!")
        return redirect('products:admin_product_list')
    
    else:
        categories = Category.objects.all()
        brands = Brand.objects.all()
        return render(request, 'products/edit_product.html', {
            'product': product,
            'categories': categories,
            'brands': brands,
            'product_images': product.images.all(),
            'variants': product.variants.all()  # Send existing variants for management
        })


from django.core.paginator import Paginator
from django.db.models import Q

@role_required(['admin'])
def product_list_admin(request):
    search_query = request.GET.get('search', '')
    
    products = Product.objects.all()

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

# @role_required(allowed_roles=['admin'])
# def delete_image(request, pk):
#     image = get_object_or_404(ProductImage, pk=pk)
#     product = image.product
#     try:
#         image.delete()
#         messages.success(request, 'Image deleted successfully.')
#     except Exception as e:
#         messages.error(request, f'Error deleting image: {str(e)}')
    
#     return redirect(request.META.get('HTTP_REFERER', 'products:edit_product', args=[product.id]))


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


@role_required(allowed_roles=['admin'])
def add_variant(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        variant_name = request.POST.get("variant_name", "").strip()
        price = request.POST.get("price")
        discount = request.POST.get("discount", "0")
        stock = request.POST.get("stock")
        is_default = request.POST.get("is_default") == "on"

        if not variant_name:
            messages.error(request, "Variant name cannot be empty.")
            return redirect("products:edit_product", product_id=product.id)

        try:
            price = float(price)
            discount = float(discount)
            stock = int(stock)
            if price <= 0:
                messages.error(request, "Price must be positive.")
                return redirect("products:edit_product", product_id=product.id)
            if discount > price:
                messages.error(request, "Discount cannot exceed price.")
                return redirect("products:edit_product", product_id=product.id)
            if stock < 0:
                messages.error(request, "Stock cannot be negative.")
                return redirect("products:edit_product", product_id=product.id)
        except ValueError:
            messages.error(request, "Invalid values for price, discount, or stock.")
            return redirect("products:edit_product", product_id=product.id)

        ProductVariant.objects.create(
            product=product,
            variant_name=variant_name,
            price=price,
            discount=discount,
            stock=stock,
            is_default=is_default
        )
        messages.success(request, "Variant added successfully.")
        return redirect("products:edit_product", product_id=product.id)

    return render(request, "products/add_variant.html", {"product": product})


@role_required(allowed_roles=['admin'])
def edit_variant(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    if request.method == "POST":
        variant.variant_name = request.POST.get("variant_name", "").strip()
        price = request.POST.get("price")
        discount = request.POST.get("discount", "0")
        stock = request.POST.get("stock")
        variant.is_default = request.POST.get("is_default") == "on"
        try:
            price = float(price)
            discount = float(discount)
            stock = int(stock)
            if price <= 0:
                messages.error(request, "Price must be positive.")
                return redirect("products:edit_variant", variant_id=variant.id)
            if discount > price:
                messages.error(request, "Discount cannot exceed price.")
                return redirect("products:edit_variant", variant_id=variant.id)
            if stock < 0:
                messages.error(request, "Stock cannot be negative.")
                return redirect("products:edit_variant", variant_id=variant.id)
        except ValueError:
            messages.error(request, "Invalid values for price, discount, or stock.")
            return redirect("products:edit_variant", variant_id=variant.id)
        
        variant.price = price
        variant.discount = discount
        variant.stock = stock
        variant.save()
        messages.success(request, "Variant updated successfully.")
        return redirect("products:edit_product", product_id=variant.product.id)
    
    return render(request, "products/edit_variant.html", {"variant": variant})


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
        products = products.order_by('-rating')
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
