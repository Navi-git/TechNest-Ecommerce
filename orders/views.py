from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.crypto import get_random_string
from datetime import datetime

# Import your models – update the paths as required
from cart.models import Cart, CartItem
from user_panel.models import UserAddress 
from .models import OrderAddress, OrderMain, OrderSub, ReturnRequest
from payments.models import *

from userauths.decorators import role_required 
from datetime import timedelta

from coupons.utils import *
from coupons.models import *
from payments.utils import process_wallet_payment




@role_required('customer')
def order_verification_view(request):
    if request.method == "GET":
        return redirect('cart:checkout')
    
    if request.method == "POST":
        current_user = request.user
        
        # 1) Get the cart and cart items
        try:
            cart = Cart.objects.get(user=current_user)
        except Cart.DoesNotExist:
            messages.error(request, "Cart not found.")
            return redirect('cart:checkout')
        
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('cart:checkout')
        
        # 2) Get selected address
        try:
            address = UserAddress.objects.get(user=current_user, order_status=True, is_deleted=False)
        except UserAddress.DoesNotExist:
            messages.error(request, 'Please select an address.')
            return redirect('cart:checkout')
        

        
        # 3) Validate each cart items stock
        for cart_item in cart_items:
            if cart_item.variant.stock < cart_item.quantity:
                messages.error(request, 'One or more items are out of stock.')
                return redirect('cart:checkout')
            
            if address.status:
                messages.error(request, 'Please select a valid address.')
                return redirect('cart:checkout')
            
            if not cart_item.product.is_active:
                messages.error(request, 'One or more products are inactive.')
                return redirect('cart:checkout')
        
        # 4) Calculate total before  coupon discounts
        total_amount = sum(item.total_cost() for item in cart_items)
        cart_total = cart.get_subtotal()
        total = cart.get_total()

        final_amount = total
        discount_amount = sum((item.variant.price - item.get_unit_price()) * item.quantity for item in cart.items.filter(is_active=True))
        discount_coupon = 0


        # --------------------- Coupon Logic Start ---------------------
        coupon_code = request.session.get('applied_coupon')
        coupon = None

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code, status=True)
                now = timezone.now()

                if not (coupon.valid_from <= now <= coupon.valid_to):
                    messages.error(request, 'Coupon has expired.')
                    return redirect('cart:checkout')

                if CouponUser.objects.filter(user=current_user, coupon=coupon).exists():
                    messages.error(request, 'You have already used this coupon.')
                    return redirect('cart:checkout')

                discount_coupon = cart_total * coupon.discount / 100
                if discount_coupon > coupon.maximum_discount:
                    discount_coupon = coupon.maximum_discount

                discount_amount += discount_coupon
                final_amount -= discount_coupon

            except Coupon.DoesNotExist:
                messages.error(request, 'Invalid coupon.')
                return redirect('cart:checkout')
        # --------------------- Coupon Logic End ---------------------

        # 5) Payment option & COD check
        payment_option = request.POST.get('payment_option')
        if payment_option is None:
            messages.error(request, 'Select Payment Option')
            return redirect('cart:checkout')
        
        # Optional: For COD, check additional conditions
        if payment_option == "Cash On Delivery" and final_amount > 1000:
            messages.error(request, 'COD only available for orders up to ₹1000 after discounts.')
            return redirect('cart:checkout')
        
        #6) Create a new order address based on the user's selected address
        order_address = OrderAddress.objects.create(
            name=address.name,
            house_name=address.house_name,
            street_name=address.street_name,
            pin_number=address.pin_number,
            district=address.district,
            state=address.state,
            country=address.country,
            phone_number=address.phone_number
        )

        # 7) Helper to generate unique IDs for order and payment
        def gen_id(prefix_len=4, dt_fmt="%H%M%S%Y"):
            now = datetime.now()
            part = now.strftime(dt_fmt)
            uniq = get_random_string(length=prefix_len, allowed_chars='1234567890')
            return f"{current_user.id}{part}{uniq}"

        order_id = gen_id(4, "%H%M%S%Y")
        payment_id = gen_id(2, "%m%Y%H%S")

        # 8) Branch by payment type
        if payment_option == "Online Payment":
            # create a PENDING OrderMain so process_payment can look it up
            order_main = OrderMain.objects.create(
                user=current_user,
                address=order_address,
                total_amount=total_amount,
                final_amount=final_amount,
                discount_amount=discount_amount,
                payment_option=payment_option,
                order_id=order_id,
                order_status="Pending",
                payment_status=False,
            )
            # store invoice items + coupon in session for later suborder creation
            request.session['pending_order_items'] = [
                {'variant_id': i.variant.id, 'quantity': i.quantity} for i in cart_items
            ]
            request.session['pending_coupon_code'] = coupon_code
            # clear coupon session (will re-populate on failure)
            request.session.pop('applied_coupon', None)

            request.session['order_id'] = order_main.order_id
            request.session['order_date'] = order_main.date.strftime("%Y-%m-%d")
            request.session['order_status'] = order_main.order_status

            return redirect('payments:process_payment', order_id=order_main.order_id)
        
        # If Wallet payment, process through wallet utility
        elif payment_option == "Wallet":
            success, msg = process_wallet_payment(current_user, final_amount)
            if not success:
                messages.error(request, msg)
                return redirect('cart:checkout')

            # Now payment is confirmed — create the order fully
            order_main = OrderMain.objects.create(
                user=current_user,
                address=order_address,
                total_amount=total_amount,
                final_amount=final_amount,
                discount_amount=discount_amount,
                payment_option=payment_option,
                order_id=order_id,
                order_status="Confirmed",
                payment_status=True,
            )

            # Sub-orders & stock
            for item in cart_items:
                OrderSub.objects.create(
                    user=current_user,
                    main_order=order_main,
                    variant=item.variant,
                    price=item.variant.discount,
                    quantity=item.quantity,
                )
                item.variant.stock -= item.quantity
                item.variant.save()

            # Mark coupon used
            if coupon:
                CouponUser.objects.create(user=current_user, coupon=coupon, used = True, order_id = order_main.order_id)

            # Clear cart & session
            cart_items.delete()
            request.session.pop('applied_coupon', None)

            request.session['order_id'] = order_main.order_id
            request.session['order_date'] = order_main.date.strftime("%Y-%m-%d")
            request.session['order_status'] = order_main.order_status

            messages.success(request, 'Order placed successfully via Wallet.')
            return redirect('order:order_success')

        else:  # Cash On Delivery
            order_main = OrderMain.objects.create(
                user=current_user,
                address=order_address,
                total_amount=total_amount,
                final_amount=final_amount,
                discount_amount=discount_amount,
                payment_option=payment_option,
                order_id=order_id,
                order_status="Confirmed",
                payment_status=False,
            )

            # Sub-orders & stock
            for item in cart_items:
                OrderSub.objects.create(
                    user=current_user,
                    main_order=order_main,
                    variant=item.variant,
                    price=item.variant.discount,
                    quantity=item.quantity,
                )
                item.variant.stock -= item.quantity
                item.variant.save()

            if coupon:
                CouponUser.objects.create(user=current_user, coupon=coupon, used = True, order_id = order_main.order_id)

            cart_items.delete()
            request.session.pop('applied_coupon', None)

            request.session['order_id'] = order_main.order_id
            request.session['order_date'] = order_main.date.strftime("%Y-%m-%d")
            request.session['order_status'] = order_main.order_status

            messages.success(request, 'Order placed successfully.')
            return redirect('order:order_success')
        




from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

@login_required
@role_required('customer')  
def order_success(request):
    future_date_time = timezone.now() + timedelta(days=5)
    formatted_future_date = future_date_time.strftime("Arriving By %d %a %B %Y")
    order_id = request.session.get('order_id', None)
    date = request.session.get('order_date', None)
    order_status = request.session.get('order_status', None)
    
    context = {
        'formatted_future_date': formatted_future_date,
        'order_id': order_id,
        'date': date,
        'order_status': order_status,
    }
    return render(request, 'orders/order.html', context)


@role_required('customer')
def order_failure(request):
    order_id = request.session.get('order_id', None)
    date = request.session.get('order_date', None)
    order_status = request.session.get('order_status', None)
    order = OrderMain.objects.get(order_id=order_id)
    
    # You can add a failure-specific message or additional context as needed.
    failure_message = "Unfortunately, your payment was not successful. Please try again or contact support."
    order_status = "Failed"
    order.order_status = order_status
    order.save()

    context = {
        'order_id': order_id,
        'date': date,
        'order_status': order_status,
        'failure_message': failure_message,
    }
    return render(request, 'orders/order_fail.html', context)


from django.core.paginator import Paginator


@role_required('admin')
def admin_order(request):
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()

    orders = OrderMain.objects.all().order_by('-updated_at')

    if search_query:
        orders = orders.filter(order_id__icontains=search_query)

    if status_filter and status_filter != 'Show all':
        if status_filter == 'Active':
            orders = orders.filter(is_active=True)
        elif status_filter == 'Inactive':
            orders = orders.filter(is_active=False)

    # Pagination: show 5 orders per page
    paginator = Paginator(orders, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'orders/admin_order.html', context)



@role_required('admin')
def admin_order_details(request, pk):
    order_main = get_object_or_404(OrderMain, id=pk)
    order_sub = OrderSub.objects.filter(main_order=order_main)
    return render(request, 'orders/admin_order_details.html', {
        'orders': order_main,
        'order_sub': order_sub,
    })


from django.http import HttpResponse

@role_required('admin')
def order_status(request, pk):
    if request.method == "POST":
        order = get_object_or_404(OrderMain, id=pk)
        new_status = request.POST.get('order_status')
        if new_status == 'Delivered':
            order.order_status = new_status
            order.payment_status = True
            order.save()
            messages.success(request, 'Order payment completed & status updated as Delivered.')
            return redirect('order:admin_orders_details', pk)
        elif new_status:
            order.order_status = new_status
            order.save()
            messages.success(request, 'Order status updated.')
            return redirect('order:admin_orders_details', pk)
        else:
            messages.error(request, 'Some error occured during status update')
            return HttpResponse("No status selected", status=400)
    else:
        messages.info(request, 'Not the expected request method.')
        return HttpResponse("Method not allowed", status=405)


from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import OrderMain, OrderSub

@role_required('customer')
def cancel_order(request, pk):
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    try:
        order = OrderMain.objects.get(id=pk, user=request.user)
    except OrderMain.DoesNotExist:
        messages.error(request, 'Order does not exist.')
        return redirect('user_panel:user_dash')

    # If the order was already fully canceled, exit early.
    if not order.is_active:
        messages.error(request, 'Order has already been canceled.')
        return redirect('user_panel:user_dash')

    # Fetch all sub-items (including those already refunded / is_active=False).
    all_items = OrderSub.objects.filter(main_order=order)

    # 1) Compute the original "cart total" at time of ordering.
    #    This must include every OrderSub of that main_order, regardless of is_active.
    original_cart_total = sum(item.final_total_cost() for item in all_items)

    if original_cart_total <= 0:
        # (This shouldn’t normally happen, but guard against division by zero.)
        messages.error(request, 'Cannot compute refund: invalid order totals.')
        return redirect('user_panel:user_dash')

    # 2) Find which sub-items are still active (i.e. not individually canceled already).
    remaining_items = all_items.filter(is_active=True)
    if not remaining_items.exists():
        # If every single item was already canceled individually, there is nothing left to refund here.
        messages.error(request, 'All items in this order have already been refunded individually.')
        return redirect('user_panel:user_dash')

    # 3) Calculate "remaining_total" = sum(final_total_cost()) of only the still‑active items.
    remaining_total = sum(item.final_total_cost() for item in remaining_items)

    # 4) Compute how much we need to refund now:
    #    ratio_of_remaining = remaining_total / original_cart_total
    #    refund_amount = order.final_amount * ratio_of_remaining
    refund_amount = (order.final_amount * remaining_total) / original_cart_total

    # 5) Restock + mark each remaining item inactive:
    for item in remaining_items:
        variant = item.variant
        variant.stock += item.quantity
        variant.save()

        item.is_active = False
        item.save()

    # 6) Mark the main order itself as canceled:
    order.order_status = "Canceled"
    order.is_active = False
    order.save()

    # 7) Credit exactly "refund_amount" to the wallet (same pattern you used before):
    wallet, _ = Wallet.objects.get_or_create(user=order.user)
    wallet.credit(
        refund_amount,
        order=item, 
        description=f"Refund for fully canceled order #{order.order_id}"
    )

    messages.success(
        request,
        f"Order canceled successfully. ₹{refund_amount:.2f} has been refunded to your wallet.")
    return redirect('user_panel:user_dash')


@role_required('admin')
def admin_cancel_order(request, pk):
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)
    
    try:
        order = OrderMain.objects.get(id=pk)
        order_items = OrderSub.objects.filter(main_order=order, is_active=True)
        
        # Increase the variant stock for each order item and mark the item inactive.
        for order_item in order_items:
            order_variant = order_item.variant
            order_variant.stock += order_item.quantity
            order_variant.save()
            order_item.is_active = False
            order_item.save()
        
        # Update order status.
        order.order_status = "Canceled"
        order.is_active = False
        order.save()

        if order.payment_status:
            wallet = Wallet.objects.get(user=order.user)
            wallet.credit(order.final_amount, order=order_item, description=f"Refund for order #{order.order_id}. The order is cancelled due to unfoseen difficulties." )
            order.payment_status=False
            order.save()
            messages.success(request, "Order canceled and amount refunded successfully.")
            return redirect('order:admin_orders_details', pk=order.id)
        else:
            messages.success(request, "Order canceled successfully. No refund was required.")
            return redirect('order:admin_orders_details', pk=order.id)
    
    except OrderMain.DoesNotExist:
        messages.error(request, "Order does not exist.")
        return redirect('order:admin_orders_details', pk=pk)
    



@role_required('customer')
def return_order(request, pk):
    if request.method != "POST":
        return redirect('user_panel:user_dash')
    
    try:
        order = get_object_or_404(OrderMain, id=pk)
        order_items = OrderSub.objects.filter(main_order=order)
        
        if not order.is_active:
            messages.error(request, 'Order is already returned.')
            return redirect('user_panel:user_dash')
        
        if order.order_status in ['Pending', 'Confirmed', 'Shipped']:
            messages.error(request, 'Order cannot be returned at this stage.')
            return redirect('user_panel:user_dash')
        
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, 'A reason must be provided for returns.')
            return redirect('user_panel:user_dash')
        
        ReturnRequest.objects.create(
            order_main=order,
            reason=reason
        )
        
        # Optionally update the order status if needed.
        order.order_status = "Pending"
        order.save()
        
        messages.success(request, "Please wait for the admin's approval.")
        return redirect('user_panel:user_dash')
    
    except OrderMain.DoesNotExist:
        messages.error(request, "Order does not exist.")
        return redirect('user_panel:user_dash')
    
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")
        return redirect('user_panel:user_dash')



@role_required('admin')
def admin_return_requests(request):
    search_query = request.GET.get('search', '').strip()

    if search_query:
        return_requests = ReturnRequest.objects.filter(order_main__order_id__icontains=search_query).order_by('-created_at')
    else:
        return_requests = ReturnRequest.objects.all().order_by('-created_at')

    # Pagination: show 5 return requests per page
    paginator = Paginator(return_requests, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'return_requests': page_obj,
        'search_query': search_query,
    }
    return render(request, 'orders/return_request.html', context)


@role_required('admin')
def admin_return_approval(request, pk):
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    return_request = get_object_or_404(ReturnRequest, id=pk)
    action = request.POST.get('action')

    if action == 'Approve':
        return_request.status = "Approved"
        return_request.save()

        # ----- Individual‐item return -----
        if return_request.order_sub:
            item = return_request.order_sub
            main_order = item.main_order

            # 1) Mark the item as returned/inactive
            item.is_active = False
            item.status = "Returned"
            item.save()

            # 2) Restock that variant
            variant = item.variant
            variant.stock += item.quantity
            variant.save()

            # 3) Compute prorated refund for this single item,
            #    exactly as you already had:
            product_amount = item.final_total_cost()
            cart_total = sum(
                i.final_total_cost()
                for i in OrderSub.objects.filter(main_order_id=main_order.id)
            )
            if cart_total > 0:
                product_percent = (product_amount / cart_total) * 100
                refund_amount = (main_order.final_amount * product_percent) / 100
            else:
                refund_amount = 0

            # 4) Credit only that prorated amount
            if main_order.payment_status:
                wallet = Wallet.objects.get(user=main_order.user)
                wallet.credit(
                    refund_amount,
                    order=item,
                    description=f"Refund for returned item #{item.id}"
                )

            # 5) If no active sub‐items remain, mark the order itself as 'Returned'
            if not main_order.ordersub_set.filter(is_active=True).exists():
                main_order.order_status = 'Returned'
                main_order.save()

            messages.success(request, "Return request approved. Refund is credited to your wallet.")
            return redirect('order:return_requests')

        # ----- Full‐order return (no order_sub attached) -----
        else:
            order = return_request.order_main

            # 1) Collect all OrderSub for this order (active + already returned)
            all_items = OrderSub.objects.filter(main_order=order)

            # 2) Compute original cart total (sum of every line’s final_total_cost)
            original_cart_total = sum(i.final_total_cost() for i in all_items)
            if original_cart_total <= 0:
                # Safety check—you shouldn’t normally hit this.
                messages.error(request, "Invalid order totals; cannot compute refund.")
                return redirect('order:return_requests')

            # 3) Find only those sub‐items still active (i.e. not individually returned yet)
            remaining_items = all_items.filter(is_active=True)
            if not remaining_items.exists():
                # If every item was already returned, there’s nothing left to refund here.
                messages.error(request, "All items in this order have already been returned.")
                return redirect('order:return_requests')

            # 4) Compute remaining_total = sum of final_total_cost() for active items
            remaining_total = sum(i.final_total_cost() for i in remaining_items)

            # 5) Prorated refund: give the order the “rest” of its order_final_amount
            refund_amount = (order.final_amount * remaining_total) / original_cart_total

            # 6) Restock & mark inactive each remaining item
            for item in remaining_items:
                # a) Restock
                var = item.variant
                var.stock += item.quantity
                var.save()

                # b) Mark returned
                item.is_active = False
                item.status = "Returned"
                item.save()

            # 7) Mark the main order itself as Returned
            order.order_status = 'Returned'
            order.is_active = False
            order.save()

            # 8) Only credit the prorated refund if payment was already captured
            if order.payment_status:
                wallet = Wallet.objects.get(user=order.user)
                wallet.credit(
                    refund_amount,
                    order=None,
                    description=f"Refund for returned order #{order.order_id}"
                )
                messages.success(
                    request,
                    f"Return request approved. ₹{refund_amount:.2f} has been refunded to the wallet."
                )
            else:
                messages.success(request, "Return request approved.")
            return redirect('order:return_requests')

    elif action == "Reject":
        return_request.status = "Rejected"
        return_request.save()

        # If it was an individual‐item request, also update that sub‐item’s status
        if return_request.order_sub:
            return_request.order_sub.status = "Return Rejected"
            return_request.order_sub.save()

        # Reset main order’s status back to “Delivered”
        return_request.order_main.order_status = 'Delivered'
        return_request.order_main.save()

        messages.success(request, "Return request rejected.")
        return redirect('order:return_requests')

    else:
        messages.error(request, "Invalid action.")
        return redirect('order:return_requests')


@role_required('customer')
def individual_cancel(request, pk):
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)
    
    order_sub = get_object_or_404(OrderSub, id=pk, user=request.user)
    
    if not order_sub.is_active:
        messages.error(request, 'Order item is already canceled.')
        return redirect('user_panel:user_dash')
    
    if order_sub.main_order.order_status not in ['Pending', 'Confirmed', 'Shipped', 'Delivered']:
        messages.error(request, 'Order cannot be canceled at this stage.')
        return redirect('user_panel:user_dash')
    
    # --------- PARTIAL (PER‐ITEM) REFUND ----------
    if order_sub.main_order.payment_status == True:
        product_amount = order_sub.final_total_cost()  
        cart_total = sum(i.final_total_cost() for i in OrderSub.objects.filter(main_order_id = order_sub.main_order.id)) 
        product_percent = (product_amount/cart_total )*100 
        refund_amount = order_sub.main_order.final_amount * product_percent / 100
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        wallet.credit(refund_amount, order=order_sub, description="Refund for canceled product (OrderItem #{order_sub.id})")

    order_sub.is_active = False
    order_sub.save()
    
    # --------- IF ALL ITEMS ARE NOW CANCELED, JUST UPDATE MAIN ORDER STATUS ----------
    last_item = not order_sub.main_order.ordersub_set.filter(is_active=True).exists()
    if last_item:
        # Only change status; do NOT issue another refund here.
        order_sub.main_order.order_status = "Canceled"
        order_sub.main_order.save()
    
    # Restore the variant's stock and update item status.
    order_sub.variant.stock += order_sub.quantity
    order_sub.status = "Canceled"
    order_sub.variant.save()

    
    
    messages.success(request, 'Order item canceled successfully.')
    return redirect('user_panel:user_dash')


@role_required('customer')
def individual_return(request, pk):
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)
    
    order_sub = get_object_or_404(OrderSub, id=pk, user=request.user)
    
    if not order_sub.is_active:
        messages.error(request, 'Order item is already Returned.')
        return redirect('user_panel:user_dash')
    
    if order_sub.main_order.order_status in ['Pending', 'Confirmed', 'Shipped', 'Canceled']:
        messages.error(request, 'Order cannot be returned at this stage.')
        return redirect('user_panel:user_dash')
    
    reason = request.POST.get('reason', '').strip()
    if not reason:
        messages.error(request, 'A reason must be provided for returns.')
        return redirect('user_panel:user_dash')
    
    ReturnRequest.objects.create(
        order_main=order_sub.main_order,
        order_sub=order_sub,
        reason=reason
    )
    
    order_sub.status = "Return Requested"
    order_sub.save()
    
    messages.success(request, "Please wait for the admin's approval.")
    return redirect('user_panel:user_dash')
