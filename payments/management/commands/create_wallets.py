from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from payments.models import Wallet

class Command(BaseCommand):
    help = 'Create wallets for all existing users who do not have one.'

    def handle(self, *args, **options):
        User = get_user_model()
        for user in User.objects.all():
            if not Wallet.objects.filter(user=user).exists():
                Wallet.objects.create(user=user)
                self.stdout.write(f'Wallet created for user: {user.username}')
        self.stdout.write('✅ Wallet creation for existing users completed.')
