import random  # For generating the 6-digit OTP
from django.core.mail import send_mail  # For sending emails
from .models import OTP  # Import the OTP model to store OTP data


def send_otp(email, user):
    otp_code = random.randint(100000, 999999)  # Generate a 6-digit OTP

    # Save OTP to the database
    OTP.objects.create(user=user, code=otp_code)  # Correct usage of 'user'

    # Send email
    subject = "Your OTP Code"
    message = f"Your OTP code is {otp_code}. Please use it within 5 minutes."
    from_email = "your_email@example.com"  # Replace with your email
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)

    return otp_code

