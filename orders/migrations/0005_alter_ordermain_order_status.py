# Generated by Django 5.1.4 on 2025-04-24 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_ordermain_payment_id_alter_ordermain_payment_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordermain',
            name='order_status',
            field=models.CharField(default='Delivered', max_length=100),
        ),
    ]
