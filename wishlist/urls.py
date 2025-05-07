from django.urls import path
from . import views

app_name = "wishlist"

urlpatterns = [
    path('', views.wishlist_view, name='wishlist'),
    path('add/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('move-to-cart/', views.wishlist_to_cart, name='wishlist_to_cart'),
]
