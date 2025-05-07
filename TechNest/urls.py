"""
URL configuration for TechNest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),  # Default Django admin
    path('', include('homeapp.urls')),  # Home app URLs
    path('auths/', include('userauths.urls')),  # Custom admin panel
    path('accounts/', include('allauth.urls')),  # Allauth URLs
    path('categories/', include('category.urls')),  # Category URLs
    path('products/', include('products.urls')),  # Product URLs
    path('cart/', include('cart.urls')), # Cart URLs
    path('user_panel/',include('user_panel.urls')), # User Profile and settings URLs
    path('orders/', include('orders.urls')),  # Order URLs
    path('coupons/', include('coupons.urls')), # Coupon URLs
    path('payments/', include('payments.urls')), # Payment URLs
    path('wishlist/', include('wishlist.urls')), # Wishlist URLs

    path("", include("accounts.urls")),
]

# Serving static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
