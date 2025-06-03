from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Cart, CartItem
from products.models import ProductVariant
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.decorators.http import require_POST
from user_panel.models import UserAddress  
from coupons.utils import get_available_coupons_for_user

from userauths.decorators import role_required
def get_user_cart(request):
    """Retrieve or create a cart for an authenticated user."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    return None


def cart_detail(request):
    """Render the cart details page with product images and updated pricing summary."""
    cart = get_user_cart(request)
    if not cart:
        return render(request, 'cart/cart_detail.html', {'cart': None})
    
    # Retrieve only active cart items
    cart_items = cart.items.filter(is_active=True)
    for cart_item in cart_items:
        product = cart_item.variant.product  # Get product from variant
        first_image = product.images.first()  # Fetch first product image
        cart_item.thumbnail = first_image.image if first_image else None

    # Subtotal is calculated using the discounted (final) unit price for each item
    subtotal = cart.get_subtotal()  # This sums item.get_total_price() for active items

    # Shipping cost based on the subtotal
    shipping_cost = cart.get_shipping_cost()

    # Calculate the total product discount amount:
    # For each item, discount is (regular price - final price) * quantity.
    discount_amount = sum(
        (item.variant.price - item.get_unit_price()) * item.quantity for item in cart_items
    )
    
    # Calculate an overall effective discount percentage based on original total
    original_total = subtotal + discount_amount  # Original total before discount
    discount_percentage = ((discount_amount / original_total )* 100) if original_total > 0 else 0

    # Final total is the subtotal (with discounts already applied) plus shipping.
    total = cart.get_subtotal() + cart.get_shipping_cost()

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'discount_amount': discount_amount,
        'discount_percentage': discount_percentage,
        'total': total,
    }
    return render(request, 'cart/cart_detail.html', context)




# @require_POST
# def add_to_cart(request, product_id):
#     """Add a product variant to the cart."""
#     if not request.user.is_authenticated:
#         return redirect('account_login')  # Redirect to login if user is not authenticated

#     variant_id = request.POST.get('variant_id')
#     quantity = int(request.POST.get('quantity', 1))

#     variant = get_object_or_404(ProductVariant, id=variant_id)
#     product = variant.product

#     cart = get_user_cart(request)
#     if not cart:
#         return redirect('account_login')

#     cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, variant=variant)

#     if not created:
#         cart_item.quantity += quantity
#     else:
#         cart_item.quantity = quantity

    
#     cart_item.save()
#     return redirect('cart:cart_detail')


from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import * 
from products.models import *

@require_POST
def add_to_cart(request, product_id):
    """Add a product variant to the cart."""
    if not request.user.is_authenticated:
        return redirect('account_login')  # Redirect to login if user is not authenticated

    variant_id = request.POST.get('variant_id')
    quantity = int(request.POST.get('quantity', 1))

    variant = get_object_or_404(ProductVariant, id=variant_id)
    product = variant.product

    cart = get_user_cart(request)
    if not cart:
        return redirect('account_login')

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, variant=variant)

    # Calculate total quantity if this product is already in cart
    new_quantity = cart_item.quantity + quantity if not created else quantity

    # Enforce max purchase limit
    if new_quantity > 5:
        messages.error(request, "You can only purchase up to 5 units of this product.")
        return redirect('cart:cart_detail')

    # Enforce stock availability
    if new_quantity > variant.stock:
        messages.error(request, f"Only {variant.stock} unit(s) available in stock.")
        return redirect('cart:cart_detail')

    # All checks passed, update quantity
    cart_item.quantity = new_quantity
    cart_item.save()

    messages.success(request, "Item added to cart successfully.")
    return redirect('cart:cart_detail')



@csrf_exempt
def update_cart_item(request, item_id):
    """Update the quantity of a cart item and return updated totals."""
    if request.method == "POST":
        data = json.loads(request.body)
        new_quantity = int(data.get("quantity", 1))

        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user, is_active=True)
            cart_item.quantity = new_quantity
            cart_item.save()

            # Re-fetch cart and items
            cart = get_user_cart(request)
            items = cart.items.filter(is_active=True)

            # 1) item total
            item_total = cart_item.get_total_price()

            # 2) cart subtotal
            subtotal = cart.get_subtotal()

            # 3) shipping cost
            shipping_cost = cart.get_shipping_cost()

            # 4) discount amount
            discount_amount = sum(
                (i.variant.price - i.get_unit_price()) * i.quantity
                for i in items
            )

            # 5) discount percentage
            original_total = subtotal + discount_amount
            discount_percentage = (discount_amount / original_total * 100) if original_total > 0 else 0

            # 6) final total
            total = subtotal - discount_amount + shipping_cost

            return JsonResponse({
                "success": True,
                "item_total": f"{item_total:.2f}",
                "subtotal": f"{subtotal:.2f}",
                "shipping_cost": shipping_cost,              # send numeric; your JS reads data-cost
                "discount_amount": f"{discount_amount:.2f}",
                "discount_percentage": f"{discount_percentage:.2f}",
                "total": f"{total:.2f}",
            })

        except CartItem.DoesNotExist:
            return JsonResponse({"success": False, "error": "Item not found"}, status=404)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


def remove_cart_item(request, item_id):
    """Remove a cart item completely."""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('cart:cart_detail')


def clear_cart(request):
    """Clear all items from the cart."""
    cart = get_user_cart(request)
    if cart:
        cart.items.all().delete()
    return redirect('cart:cart_detail')



from coupons.utils import calculate_coupon_discount
from coupons.models import *

@role_required(['customer','admin'])
def checkout(request):
    # Ensure user is authenticated
    if not request.user.is_authenticated:
        return redirect('account_login')
    
    # Get or create the user's cart
    cart = get_user_cart(request)
    if not cart or not cart.items.filter(is_active=True).exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart:cart_detail')
    
    cart_items = CartItem.objects.filter(cart=cart, is_active=True)

    # ✅ Validate quantity limits before proceeding
    for item in cart_items:
        if item.quantity > item.variant.stock:
            messages.error(request, f"Not enough stock for {item.product.name}. Available: {item.variant.stock}")
            return redirect('cart:cart_detail')
        if item.quantity > 5:
            messages.error(request, f"You can only purchase up to 5 units of {item.product.name}.")
            return redirect('cart:cart_detail')

    # Continue as normal if validation passes
    cart_total = cart.get_subtotal()

    discount_amount_bc = sum(
        (item.variant.price - item.get_unit_price()) * item.quantity for item in cart.items.filter(is_active=True)
    )

    total = cart.get_total()

    # pull user available coupons using helper function
    available_coupons = get_available_coupons_for_user(request.user)

    coupon_code = request.session.get('applied_coupon')
    discount_coupon = 0
    cart_total_cost = sum(item.total_cost() for item in cart_items)
    
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code, status=True)
            if cart_total_cost > coupon.minimum_purchase:
                discount_coupon = cart_total * coupon.discount / 100
                if discount_coupon > coupon.maximum_discount:
                    discount_coupon = coupon.maximum_discount
        except Coupon.DoesNotExist:
            discount_coupon = 0

    total = total - discount_coupon
    discount = discount_amount_bc + discount_coupon

    # Retrieve user's saved addresses using the UserAddress model
    addresses = UserAddress.objects.filter(user=request.user, is_deleted=False)

    # You may need to pass context here for rendering the template
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'discount': discount,
        'total': total,
        'addresses': addresses,
        'available_coupons': available_coupons,
        'applied_coupon': coupon_code,
        'subtotal' : cart.get_subtotal(),
        'shipping_cost' : cart.get_shipping_cost(),
        'coupons': available_coupons,
    }

    return render(request, 'cart/checkout.html', context)



from django.http import JsonResponse

@role_required(['customer'])
@require_POST
def apply_coupon(request):
    code = request.POST.get('coupon_code', '').strip().upper()
    now = timezone.now()

    cart = get_user_cart(request)
    cart_items = CartItem.objects.filter(cart=cart, is_active=True)
    cart_total_cost = sum(item.total_cost() for item in cart_items)
    cart_total = cart.get_subtotal()
    total = cart.get_total()

    try:
        coupon = Coupon.objects.get(
            code__iexact=code,
            status=True,
            valid_from__lte=now,
            valid_to__gte=now
        )
    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid or expired coupon.'})

    if CouponUser.objects.filter(coupon=coupon, used=True).count() >= coupon.usage_limit:
        return JsonResponse({'success': False, 'message': 'This coupon has reached its usage limit.'})

    if CouponUser.objects.filter(user=request.user, coupon=coupon, used=True).exists():
        return JsonResponse({'success': False, 'message': 'You have already used this coupon.'})

    if cart_total_cost <= coupon.minimum_purchase:
        return JsonResponse({'success': False, 'message': f'Purchase amount less than minimum purchase ₹{coupon.minimum_purchase}.'})

    discount_bc = sum((item.variant.price - item.get_unit_price()) * item.quantity for item in cart_items)
    discount_coupon = cart_total * coupon.discount / 100
    if discount_coupon > coupon.maximum_discount:
        discount_coupon = coupon.maximum_discount

    discount_total = discount_bc + discount_coupon
    final_total = total - discount_coupon

    request.session['applied_coupon'] = coupon.code

    return JsonResponse({
        'success': True,
        'message': f'Coupon {coupon.code} applied successfully!',
        'discount': discount_total,
        'total': final_total,
        'applied_coupon': coupon.code
    })



from django.views.decorators.http import require_POST

@role_required(['customer'])
@require_POST
def remove_coupon(request):
    try:
        del request.session['applied_coupon']

        cart = get_user_cart(request)
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        discount_bc = sum((item.variant.price - item.get_unit_price()) * item.quantity for item in cart_items)
        total = cart.get_total()  # total includes everything before coupon

        final_total = total  # after coupon is removed

        return JsonResponse({
            'success': True,
            'message': 'Coupon removed successfully.',
            'discount': discount_bc,  # keep variant-based discount if needed
            'total': final_total,
        })

    except KeyError:
        return JsonResponse({'success': False, 'message': 'No coupon to remove.'})
