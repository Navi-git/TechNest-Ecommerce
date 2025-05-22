from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


app_name="homeapp"

urlpatterns = [
    path('',views.index,name='home'), # Home URL
    path('about/',views.about,name='about'), # About URL
    path('contact/',views.contact,name='contact'), # Contact URL
    

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
