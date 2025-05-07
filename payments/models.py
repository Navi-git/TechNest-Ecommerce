
from django.db import models
from orders.models import OrderMain, OrderSub  # Ensure the correct import for your order model

class PaymentTransaction(models.Model):
    order = models.ForeignKey(OrderMain, on_delete=models.CASCADE, related_name='transactions')
    gateway = models.CharField(max_length=50)  #name of payment gateway
    gateway_order_id = models.CharField(max_length=100)
    payment_id = models.CharField(max_length=50, blank=True, null=True)
    payment_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order.order_id} - {self.gateway}"
    

from django.conf import settings
from django.db import models

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet"

    def credit(self, amount, order=None, description=""):
        """
        Increase the wallet balance and record a credit transaction.
        This will be used to refund an order amount or add funds.
        """
        self.balance += amount
        self.save()
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='credit',
            amount=amount,
            order=order,
            description=description
        )

    def debit(self, amount, order=None, description=""):
        """
        Decrease the wallet balance if sufficient funds are available and record a debit transaction.
        This will be used to pay for an order from the wallet.
        """
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            WalletTransaction.objects.create(
                wallet=self,
                transaction_type='debit',
                amount=amount,
                order=order,
                description=description
            )
            return True
        return False

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.ForeignKey(OrderSub, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.wallet.user.username} - {self.transaction_type} of {self.amount}"

