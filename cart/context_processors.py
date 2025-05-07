from wishlist.models import Wishlist
from .models import *

def cart_and_wishlist_counts(request):
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(cart__user=request.user, is_active=True).count()
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
    else:
        cart_count = 0
        wishlist_count = 0

    return {
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
    }