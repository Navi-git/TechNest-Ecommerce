from django.urls import path
from .views import add_category, edit_category, toggle_category_status, list_categories, delete_category

app_name = 'category'

urlpatterns = [
    path('list/', list_categories, name='admin_category_list'),
    path('add/', add_category, name='add_category'),
    path('edit/<int:category_id>/', edit_category, name='edit_category'),
    path('toggle/<int:category_id>/', toggle_category_status, name='toggle_category_status'),
    path('delete/<int:category_id>/', delete_category, name='delete_category'),

]
