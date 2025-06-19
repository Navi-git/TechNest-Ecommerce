from django.urls import path
from .views import add_category, edit_category, toggle_category_status, list_categories, delete_category
from . import views

app_name = 'category'

urlpatterns = [
    path('list/', list_categories, name='admin_category_list'),
    path('add/', add_category, name='add_category'),
    path('edit/<int:category_id>/', edit_category, name='edit_category'),
    path('toggle/<int:category_id>/', toggle_category_status, name='toggle_category_status'),
    path('delete/<int:category_id>/', delete_category, name='delete_category'),

    #Offer on category: admin side urls
    path('category-offers/', views.list_category_offers, name='list_category_offers'),
    path('category-offers/add/', views.add_category_offer, name='add_category_offer'),
    path('category-offers/edit/<int:offer_id>/', views.edit_category_offer, name='edit_category_offer'),
    path('category-offers/delete/<int:offer_id>/', views.delete_category_offer, name='delete_category_offer'),

]
