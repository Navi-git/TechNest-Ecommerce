from django.urls import path
from .views import verify_otp

urlpatterns = [
    path("verify-otp/", verify_otp, name="verify_otp"),
]
