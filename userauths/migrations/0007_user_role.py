# Generated by Django 5.1.4 on 2025-03-06 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauths', '0006_user_otp_user_otp_sent_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('admin', 'Admin'), ('customer', 'Customer')], default='customer', max_length=20),
        ),
    ]
