# Generated migration for Location model and delivery_prices field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_voucher_discount'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='product',
            name='delivery_prices',
            field=models.JSONField(blank=True, default=dict, help_text='Delivery prices per location as {location_id: price}'),
        ),
    ]
