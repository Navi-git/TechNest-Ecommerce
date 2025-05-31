from django.shortcuts import redirect
from django.urls import reverse
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import logout
from django.contrib import messages

class OTPVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        if user.is_authenticated:
            if user.is_blocked:
                messages.error(request,"Your account has been blocked. Please contact support.")
                logout(request)
                return redirect("account_login")
            
            # Skip OTP enforcement if the user is a social login user
            if not user.is_verified:
                if SocialAccount.objects.filter(user=user, provider='google').exists():
                    user.is_verified = True
                    user.save()
                    return redirect("homeapp:home")  # Skip OTP and go to home

                if request.path not in [reverse("verify_otp"), "/accounts/login/"]:
                    return redirect("verify_otp")

        return self.get_response(request)
