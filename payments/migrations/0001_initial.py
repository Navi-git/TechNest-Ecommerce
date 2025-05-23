# Generated by Django 5.1.4 on 2025-04-02 11:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orders', '0002_orderaddress_remove_orderitem_order_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gateway', models.CharField(max_length=50)),
                ('gateway_order_id', models.CharField(max_length=100)),
                ('payment_id', models.CharField(blank=True, max_length=50, null=True)),
                ('payment_status', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='orders.ordermain')),
            ],
        ),
    ]
