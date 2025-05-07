from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

app_name="user_panel"

urlpatterns = [
    # Admin URLs

    # User URLs
    path('user_dash', views.user_dashboard, name='user_dash'),
    path('create-address/', views.create_address, name='create_address'),
    path('edit/<int:pk>/', views.edit_address, name='edit_address'),
    path('add/', views.add_address, name='add_address'),
    path('default/<int:pk>/', views.make_as_default, name='make_as_default'),
    path('delete/<int:pk>/', views.address_delete, name='address_delete'),
    path('toggle-address-status/', views.toggle_address_status, name='toggle_address_status'),
    path('user_invoice/<int:pk>/', views.user_invoice, name='user_invoice'),
    path('user_details/', views.user_details, name='user_details'),
    path('details/<int:pk>/', views.edit_details, name='edit_details'),
    path('password_change/', views.change_password, name='change_password'),


    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
