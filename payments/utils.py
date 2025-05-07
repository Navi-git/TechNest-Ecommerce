# payments/utils.py
from payments.models import Wallet, WalletTransaction # Adjust if your transaction model is in a different module

def process_wallet_payment(user, order_main, final_amount):
    """
    Process the wallet payment for an order.
    Returns a tuple: (success, message) where success is a boolean.
    """
    try:
        wallet = Wallet.objects.get(user=user)
        if final_amount <= wallet.balance:
            # Create a transaction record for the wallet
            WalletTransaction.objects.create(
                wallet=wallet,
                description="Product Purchased With Wallet",
                amount=final_amount,
                transaction_type="Debited",
            )
            # Deduct the wallet balance
            wallet.balance -= final_amount
            wallet.save()
            
            # Update the order status accordingly
            order_main.payment_status = True
            order_main.payment_option = "Wallet"
            order_main.save()
            
            return True, "Payment successful with wallet."
        else:
            return False, "Not enough money in wallet."
    except Wallet.DoesNotExist:
        return False, "Wallet does not exist for this user."
    except Exception as e:
        return False, str(e)
