import razorpay
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from orders.models import OrderMain, OrderSub
from .models import PaymentTransaction, Wallet, WalletTransaction
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from userauths.decorators import role_required

from cart.models import Cart, CartItem
from django.contrib import messages
from products.models import ProductVariant
from coupons.models import *

# Create your views here.

from django.urls import reverse




client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def process_payment(request, order_id):
    order = get_object_or_404(OrderMain, order_id=order_id)
    amount = int(order.final_amount * 100)  # Convert amount to paise

    # Create a Razorpay order
    razorpay_order = client.order.create({
        'amount': amount,
        'currency': 'INR',
        'receipt': order.order_id,
        'payment_capture': 1
    })

    # Create a PaymentTransaction record
    PaymentTransaction.objects.create(
        order=order,
        gateway='razorpay',
        gateway_order_id=razorpay_order['id']
    )

    callback_url = request.build_absolute_uri(reverse('payments:paymenthandler'))

    context = {
        'order': order,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
        'amount': amount,
        'currency': 'INR',
        'callback_url': callback_url
    }
    return render(request, 'payments/payment.html', context)



@csrf_exempt
def paymenthandler(request):
    """
    This view is called by Razorpay (or the browser is redirected here) after payment.
    It verifies the payment signature, updates the PaymentTransaction record,
    changes the corresponding OrderMain status, and then clears the user's cart.
    """
    if request.method == "POST":
        try:
            payment_id = request.POST.get('razorpay_payment_id', '')
            order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')

            # Verify the payment signature
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            client.utility.verify_payment_signature(params_dict)
            
            # Retrieve and update the PaymentTransaction record
            transaction = PaymentTransaction.objects.get(gateway_order_id=order_id)
            transaction.payment_id = payment_id
            transaction.payment_status = True
            transaction.save()

            # Update the corresponding OrderMain record
            order = transaction.order
            order.order_status = "Confirmed"
            order.payment_status = True
            order.save()

            request.session['order_id']     = order.order_id
            request.session['order_date']   = order.date.strftime("%Y-%m-%d")
            request.session['order_status'] = order.order_status


            # load items & coupon
            pending = request.session.pop('pending_order_items', [])
            code   = request.session.pop('pending_coupon_code', None)

            # 1) create sub-orders & deduct stock
            for it in pending:
                variant = ProductVariant.objects.get(id=it['variant_id'])
                OrderSub.objects.create(
                    user=order.user,
                    main_order=order,
                    variant=variant,
                    price=variant.final_price,
                    quantity=it['quantity'],
                )
                variant.stock -= it['quantity']
                variant.save()

            # 2) mark coupon used
            if code:
                coupon = Coupon.objects.get(code__iexact=code)
                CouponUser.objects.create(user=order.user, coupon=coupon, used = True, order_id = order.order_id)


            # Clear the user's cart now that the payment is verified.
            user = order.user
            try:
                cart = Cart.objects.get(user=user)
                CartItem.objects.filter(cart=cart, is_active=True).delete()

            except Cart.DoesNotExist:
                pass

            messages.success(request, "Payment successful. Your order has been placed.")
            # Redirect to order success view (in orders app)
            return redirect('order:order_success')
        except razorpay.errors.SignatureVerificationError:
            transaction = PaymentTransaction.objects.get(gateway_order_id=request.POST.get('razorpay_order_id'))
            transaction.payment_status = False
            transaction.save()
            
            order = transaction.order
            order.order_status = "Payment Failed"
            order.save()

            request.session['order_id']     = order.order_id
            request.session['order_date']   = order.date.strftime("%Y-%m-%d")
            request.session['order_status'] = order.order_status

            messages.error(request, "Payment verification failed. Please try again.")
            return redirect('order:order_failure')
        

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('order:order_failure')
    else:
        return redirect('order:order_verification_view')