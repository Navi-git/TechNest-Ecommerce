import random
from django.core.mail import send_mail
from django.utils.timezone import now
from allauth.account.forms import SignupForm
from userauths.models import User  # Import your custom user model

class CustomSignupForm(SignupForm):
    def save(self, request):
        user = super().save(request)
        user.is_verified = False  # Prevent login until OTP is verified
        user.otp = random.randint(100000, 999999)  # Generate 6-digit OTP
        user.otp_sent_at = now()
        user.save()

        send_mail(
            "Your OTP Code",
            f"Your OTP code is {user.otp}. It expires in 5 minutes.",
            "noreply@yourshop.com",
            [user.email],
            fail_silently=False,
        )
        return user
