# Migration to add unique constraint after populating order numbers

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_populate_order_numbers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(db_index=True, max_length=20, unique=True),
        ),
    ]
