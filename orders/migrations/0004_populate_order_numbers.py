# Data migration to populate existing orders with order numbers

from django.db import migrations


def populate_order_numbers(apps, schema_editor):
    """Populate order_number for all existing orders"""
    Order = apps.get_model('orders', 'Order')
    for order in Order.objects.all():
        if order.order_number == 'PP0000000000':
            # Generate PP format: PP + 10 digit number (padded with zeros)
            order.order_number = f'PP{str(order.id).zfill(10)}'
            order.save()


def reverse_populate(apps, schema_editor):
    """Reverse the population (optional)"""
    Order = apps.get_model('orders', 'Order')
    Order.objects.all().update(order_number='PP0000000000')


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_order_order_number'),
    ]

    operations = [
        migrations.RunPython(populate_order_numbers, reverse_populate),
    ]
