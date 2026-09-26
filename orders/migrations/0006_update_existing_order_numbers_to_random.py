# Migration to update existing orders from sequential to random format

from django.db import migrations
import secrets
import string


def generate_random_order_number():
    """Generate a unique random order number in format PPGxxxxxxxxxx"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(12))
    return f'PPG{random_part}'


def update_to_random_format(apps, schema_editor):
    """Update all existing orders from old PP format to new random PPG format"""
    Order = apps.get_model('orders', 'Order')

    # Get all orders with old format (starting with PP but not PPG)
    old_format_orders = Order.objects.filter(order_number__startswith='PP').exclude(order_number__startswith='PPG')

    for order in old_format_orders:
        # Generate new random order number
        order.order_number = generate_random_order_number()
        order.save()


def reverse_update(apps, schema_editor):
    """Reverse not possible - keeping new random format"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_alter_order_order_number_unique'),
    ]

    operations = [
        migrations.RunPython(update_to_random_format, reverse_update),
    ]
