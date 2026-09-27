# Generated migration for Location default_delivery_price

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_productimage'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='default_delivery_price',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Default delivery price for this location if not set per product',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(0)]
            ),
        ),
    ]
