from django.urls import path
from . import views

app_name = 'coupons'

urlpatterns=[
    # Admin urls
    path('list/',views.coupon_list, name='coupon_list'),
    path('create/',views.create_coupon, name='create_coupon'),
    path('edit/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('delete/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),

    # # User urls
    # path('apply/', views.apply_coupon, name='apply_coupon'),

]