from django.urls import path
from . import views

app_name = 'userauths'

urlpatterns = [
    path('', views.admin_login, name='admin_login'),  # Login URL
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),  # Dashboard URL
    path('admin-logout/', views.admin_logout, name='admin_logout'),  # Logout URL
    path("admin/user-management/", views.user_management, name="user_management"),
    path("admin/users/<int:user_id>/toggle-block/", views.toggle_user_block, name="toggle_user_block"),
    
    # path('signup/', views.customer_signup, name='customer_signup'),             # Signup URL
    path('verify-otp/<str:email>/', views.verify_otp, name='verify_otp'),       # Verify OTP URL
    # path('login/', views.customer_login, name='customer_login'),                # Login URL

    path('sales-report/', views.sales_report, name='sales_report'),
    path('filter/', views.order_date_filter, name='date_filter'),
    # # Paths for best selling sections
    path('best-selling-products/', views.best_selling_products, name='best_selling_products'),
    path('best-selling-category/', views.best_selling_category, name='best_selling_category'),
    path('best-selling-brands/', views.best_selling_brands, name='best_selling_brands'),
]
