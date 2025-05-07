from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    path('place-order/', views.order_verification_view, name='place_order'),
    path('order-success/', views.order_success, name='order_success'),
    path('order-failure/', views.order_failure, name='order_failure'),
    path('orders/', views.admin_order, name='admin_orders'),
    path('order_details/<int:pk>/', views.admin_order_details, name='admin_orders_details'),
    path('order_status/<int:pk>/', views.order_status, name='order_status'),
    path('cancel_order/<int:pk>/', views.cancel_order, name='cancel_order'),
    path('admin_cancel_order/<int:pk>/', views.admin_cancel_order, name='admin_cancel_order'),
    path('return_order/<int:pk>/', views.return_order, name='return_order'),
    path('return_requests/', views.admin_return_requests, name='return_requests'),
    path('admin_return_approval/<int:pk>/', views.admin_return_approval, name='admin_return_approval'),
    path('individual_cancel/<int:pk>/', views.individual_cancel, name='individual_cancel'),
    path('individual_return/<int:pk>/', views.individual_return, name='individual_return'),
    
]
 