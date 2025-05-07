from .models import *
from django.utils import timezone

from decimal import Decimal

def calculate_coupon_discount(coupon, cart_total):
    if cart_total < coupon.minimum_purchase:
        return Decimal('0.00')

    discount_amount = (cart_total * coupon.discount / 100)
    if discount_amount > coupon.maximum_discount:
        discount_amount = coupon.maximum_discount

    return discount_amount.quantize(Decimal('0.01'))  # round to 2 decimals




def get_available_coupons_for_user(user):
    now = timezone.now()
    
    # 1. Coupons that are active and within valid date range
    active_coupons = Coupon.objects.filter(
        status=True,
        valid_from__lte=now,
        valid_to__gte=now
    )

    # 2. Coupons already used by this user
    used_coupons = CouponUser.objects.filter(user=user, used=True).values_list('coupon_id', flat=True)

    # 3. Coupons that still have remaining global usage
    available_coupons = []
    for coupon in active_coupons:
        total_usage = CouponUser.objects.filter(coupon=coupon, used=True).count()
        if total_usage < coupon.usage_limit and coupon.id not in used_coupons:
            available_coupons.append(coupon)

    return available_coupons
