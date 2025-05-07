from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Wishlist
from products.models import *
from cart.models import *

@login_required
@require_POST
def add_to_wishlist(request):
    variant_id = request.POST.get('variant_id')
    if not variant_id:
        return JsonResponse({'success': False, 'message': 'No product variant specified.'})
    
    try:
        variant = ProductVariant.objects.get(id=variant_id)
    except ProductVariant.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Selected variant does not exist.'})
    
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, variant=variant)
    if created:
        message = 'Product variant added to wishlist.'
    else:
        message = 'This product variant is already in your wishlist.'
    
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    return JsonResponse({'success': True, 'message': message, 'wishlist_count': wishlist_count})



@login_required
@require_POST
def remove_from_wishlist(request):
    """
    Removes a wishlist item.
    Expects: POST data with 'variant_id'.
    """
    variant_id = request.POST.get('variant_id')
    if not variant_id:
        return JsonResponse({'success': False, 'message': 'No product variant specified.'})
    
    qs = Wishlist.objects.filter(user=request.user, variant_id=variant_id)
    if qs.exists():
        qs.delete()
        message = 'Removed from wishlist.'
    else:
        message = 'Item not found in wishlist.'
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    return JsonResponse({'success': True, 'message': message, 'wishlist_count': wishlist_count})



@login_required
@require_POST
def wishlist_to_cart(request):
    """
    Moves an item from wishlist to cart.
    """
    # Extract product_id and variant_id from the POST data.
    product_id = request.POST.get('product_id')
    variant_id = request.POST.get('variant_id')
    
    if not product_id or not variant_id:
        return JsonResponse({'success': False, 'message': 'Product or variant ID is missing.'}, status=400)
    
    # Retrieve product and variant objects from the database.
    product = get_object_or_404(Product, id=product_id)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    
    if not product.is_active:
        return JsonResponse({'success': False, 'message': 'Product is unavailable.'}, status=400)
    
    if variant.stock < 1:
        return JsonResponse({'success': False, 'message': 'Product is out of stock.'}, status=400)
    
    # Get or create the cart associated with the current user.
    # Ensure you have a get_user_cart() utility or similar for creating/retrieving the Cart.
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Try to get the cart item for the given product and variant.
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        variant=variant,
        defaults={'quantity': 1}
    )
    
    # If the cart item already exists, update the quantity.
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        message = 'Product quantity updated in cart.'
    else:
        message = 'Product added to cart successfully.'
    
    # Finally, remove the product variant from the wishlist.
    Wishlist.objects.filter(user=request.user, variant=variant).delete()
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    return JsonResponse({'success': True, 'message': message, 'wishlist_count': wishlist_count})




@login_required
def wishlist_view(request):
    """
    Render the wishlist with all wishlist items.
    """
    try:

        wishlist_items = Wishlist.objects.filter(user=request.user).select_related('variant__product')
        for item in wishlist_items:
            first_image = item.variant.product.images.first()
            item.thumbnail = first_image.image.url if first_image else 'assets/imgs/shop/product-placeholder.jpg'

        context = {
            'wishlist_items': wishlist_items,
        }
        return render(request, 'user_panel/wishlist.html', context)
    except Exception as e:
        # Optionally log your error e
        return render(request, 'user_panel/wishlist.html', {'error': str(e)})
