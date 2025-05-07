from django.db import models
from userauths.models import User
from products.models import ProductVariant

class OrderAddress(models.Model):
    name = models.CharField(max_length=50)
    house_name = models.CharField(max_length=500)
    street_name = models.CharField(max_length=500)
    pin_number = models.IntegerField()
    district = models.CharField(max_length=300)
    state = models.CharField(max_length=300)
    country = models.CharField(max_length=50, default="null")
    phone_number = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class OrderMain(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    address = models.ForeignKey(OrderAddress, on_delete=models.SET_NULL, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date = models.DateField(auto_now_add=True)
    order_status = models.CharField(max_length=100, default="Delivered")
    payment_option = models.CharField(max_length=100, default="Cash_on_delivery")
    payment_status = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=50)
    order_id = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.order_id


class OrderSub(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    main_order = models.ForeignKey(OrderMain, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=10, blank=True, null=True)

    def total_cost(self):

        return self.quantity * self.variant.discount

    def final_total_cost(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.main_order.order_id} - {self.variant}"


class ReturnRequest(models.Model):
    RETURN_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    order_main = models.ForeignKey(OrderMain, on_delete=models.CASCADE, blank=True, null=True)
    order_sub = models.ForeignKey(OrderSub, on_delete=models.CASCADE, blank=True, null=True)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=RETURN_STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        order_id = self.order_main.order_id if self.order_main else "N/A"
        return f"Return Request for Order {order_id}"
