from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path('process-payment/<str:order_id>/', views.process_payment, name='process_payment'),
    path('paymenthandler/', views.paymenthandler, name='paymenthandler'),

]