from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
from userauths.models import User

@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)
