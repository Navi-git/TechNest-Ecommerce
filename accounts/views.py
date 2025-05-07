
# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.contrib import messages
from userauths.models import User
import random
from django.core.mail import send_mail
from userauths.decorators import role_required

@role_required(['customer'])
def verify_otp(request):
    user = request.user

    
    # Redirect verified users away from OTP page
    if user.is_verified:
        return redirect("homeapp:home")  # Redirect to home page or dashboard


    if request.method == "POST":

        # 1. Gather the 6 digits from the form
        otp1 = request.POST.get('otp1', '')
        otp2 = request.POST.get('otp2', '')
        otp3 = request.POST.get('otp3', '')
        otp4 = request.POST.get('otp4', '')
        otp5 = request.POST.get('otp5', '')
        otp6 = request.POST.get('otp6', '')

        # 2. Combine them into a single string
        entered_otp = otp1 + otp2 + otp3 + otp4 + otp5 + otp6

        if str(user.otp) == entered_otp:
            user.is_verified = True  # Activate user after OTP verification
            user.save()
            messages.success(request, "OTP verified successfully.")
            return redirect("homeapp:home")  # Redirect to homepage after success
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    if not user.is_verified:
        user.otp = random.randint(100000, 999999)
        user.otp_sent_at = now()
        user.save()
        send_mail(
            "Your OTP Code",
            f"Your OTP code is {user.otp}. It expires in 2 minutes.",
            "noreply@yourshop.com",
            [user.email],
            fail_silently=False,
        )

    return render(request, "account/verify_otp.html")


def user_register(request):
    return render(request, 'account/signup.html')

def user_login(request):
    return render(request, 'account/login.html')