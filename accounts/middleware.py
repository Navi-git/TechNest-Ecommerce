from django.shortcuts import redirect
from django.urls import reverse
from allauth.socialaccount.models import SocialAccount

class OTPVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        if user.is_authenticated and not user.is_verified:
            # Skip OTP enforcement if the user is a social login user
            if SocialAccount.objects.filter(user=user, provider='google').exists():
                user.is_verified = True
                user.save()
                return redirect("homeapp:home")  # Skip OTP and go to home

            if request.path not in [reverse("verify_otp"), "/accounts/login/"]:
                return redirect("verify_otp")

        return self.get_response(request)
