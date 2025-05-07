from django.contrib.auth.backends import ModelBackend
from userauths.models import User

class OTPAuthBackend(ModelBackend):
    def user_can_authenticate(self, user):
        return True  # Allow login regardless of is_active
