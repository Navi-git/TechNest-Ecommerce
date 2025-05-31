from django.db import models
from django.contrib.auth.models import AbstractUser

from django.utils.timezone import now
from datetime import timedelta
from django.conf import settings

# Create your models here.


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_verified = models.BooleanField(default=False)  # For email/OTP verification
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_blocked = models.BooleanField(default=False)  # For block/unblock
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_sent_at = models.DateTimeField(blank=True, null=True)

    

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username
    

class OTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE , related_name='otps')
    code = models.CharField(max_length=6)  # 6-digit OTP
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        # Check if OTP is within 5 minutes of creation and not used
        expiration_time = self.created_at + timedelta(minutes=5)
        return now() <= expiration_time and not self.is_used
