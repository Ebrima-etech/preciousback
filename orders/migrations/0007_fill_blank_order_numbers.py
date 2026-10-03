# Orders saved through create_payment could end up with a blank order_number,
# which blocked every later order (order_number is unique). Give them real numbers.

import secrets
import string

from django.db import migrations


def generate_order_number():
    chars = string.ascii_uppercase + string.digits
    return 'PPG' + ''.join(secrets.choice(chars) for _ in range(12))


def fill_blank_order_numbers(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    taken = set(Order.objects.exclude(order_number='').values_list('order_number', flat=True))
    for order in Order.objects.filter(order_number=''):
        number = generate_order_number()
        while number in taken:
            number = generate_order_number()
        taken.add(number)
        Order.objects.filter(pk=order.pk).update(order_number=number)


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_update_existing_order_numbers_to_random'),
    ]

    operations = [
        migrations.RunPython(fill_blank_order_numbers, migrations.RunPython.noop),
    ]
