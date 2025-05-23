# Generated by Django 5.1.4 on 2025-02-12 07:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0016_remove_productimage_detail_view_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='productimage',
            name='detail_view',
            field=models.ImageField(blank=True, null=True, upload_to='product_images/detail/'),
        ),
        migrations.AddField(
            model_name='productimage',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to='product_images/thumbnail/'),
        ),
        migrations.AddField(
            model_name='productimage',
            name='zoom_view',
            field=models.ImageField(blank=True, null=True, upload_to='product_images/zoom/'),
        ),
    ]
