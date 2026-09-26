# Data migration to populate existing orders with random order numbers

from django.db import migrations
import secrets
import string


def generate_random_order_number():
    """Generate a unique random order number in format PPGxxxxxxxxxx"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(12))
    return f'PPG{random_part}'


def populate_order_numbers(apps, schema_editor):
    """Populate order_number for all existing orders with random numbers"""
    Order = apps.get_model('orders', 'Order')
    for order in Order.objects.all():
        if not order.order_number or order.order_number == '':
            # Generate random order number
            order.order_number = generate_random_order_number()
            order.save()


def reverse_populate(apps, schema_editor):
    """Reverse the population (optional)"""
    Order = apps.get_model('orders', 'Order')
    Order.objects.all().update(order_number='')


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_order_order_number'),
    ]

    operations = [
        migrations.RunPython(populate_order_numbers, reverse_populate),
    ]
