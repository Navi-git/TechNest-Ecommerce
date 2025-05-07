from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

app_name="products"

urlpatterns = [
    # Admin URLs
    path("list/", views.product_list_admin, name="admin_product_list"),
    path("add/", views.add_product, name="add_product"),
    path("edit/<int:product_id>/", views.edit_product, name="edit_product"),
    path("delete/<int:pk>/", views.delete_product, name="delete_product"),
    path("restore-product/<int:pk>/", views.restore_product, name="restore_product"),
    path("delete-image/<int:pk>/", views.delete_image, name="delete_image"),

    path('perm-delete/<int:pk>/', views.perm_delete_product, name='perm_delete_product'),

    path('variant/edit/<int:variant_id>/', views.edit_variant, name='edit_variant'),
    path('variant/delete/<int:variant_id>/', views.delete_variant, name='delete_variant'),

    # User URLs
    path("product/<int:product_id>/", views.product_detail, name="product_detail"),
    path("shop-list/", views.shop_list, name="shop_list"),
    path("product/<int:product_id>/review/", views.add_review, name="add_review"),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
