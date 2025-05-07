from django.urls import path
from . import views

app_name="homeapp"

urlpatterns = [
    path('',views.index,name='home'), # Home URL
    path('about/',views.about,name='about'), # About URL
    path('contact/',views.contact,name='contact'), # Contact URL
    path('on-test/',views.on_test, name='on_test'),
]
