import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


PLASTIC_TYPE_CHOICES = [
    ('PET', 'PET (1)'),
    ('HDPE', 'HDPE (2)'),
    ('PVC', 'PVC (3)'),
    ('LDPE', 'LDPE (4)'),
    ('PP', 'PP (5)'),
    ('PS', 'PS (6)'),
    ('MIXED', 'Mixed plastics'),
    ('OTHER', 'Other'),
]

AUTO_VALUE_CHOICES = [
    ('plastic_diverted_kg', 'Plastic diverted (kg)'),
    ('plastic_collected_kg', 'Plastic collected (kg)'),
    ('plastic_in_products_sold_kg', 'Recycled plastic in products sold (kg)'),
    ('co2_saved_kg', 'CO2 saved (kg)'),
    ('water_saved_liters', 'Water saved (liters)'),
    ('products_sold', 'Products sold'),
    ('items_produced', 'Items produced'),
    ('people_engaged', 'People engaged'),
    ('bottles_equivalent', 'Bottles equivalent'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('impact', '0004_alter_bulkrfq_options_remove_bulkrfq_product_items_and_more'),
        ('products', '0008_product_impact'),
        ('orders', '0006_update_existing_order_numbers_to_random'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='impactmetric',
            options={'ordering': ['order', 'id'], 'verbose_name_plural': 'Impact Metrics'},
        ),
        migrations.AlterField(
            model_name='impactmetric',
            name='value',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='impactmetric',
            name='auto_value',
            field=models.CharField(blank=True, choices=AUTO_VALUE_CHOICES, help_text='If set, the value is calculated from the impact log instead of typed in', max_length=40),
        ),
        migrations.AddField(
            model_name='impactmetric',
            name='order',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='impactmetric',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.CreateModel(
            name='ImpactEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.localdate)),
                ('source', models.CharField(choices=[('sale', 'Product sale'), ('collection', 'Plastic collection'), ('production', 'Production run'), ('event', 'Event / workshop'), ('adjustment', 'Manual adjustment')], default='collection', max_length=20)),
                ('title', models.CharField(blank=True, max_length=255)),
                ('plastic_type', models.CharField(blank=True, choices=PLASTIC_TYPE_CHOICES, max_length=20)),
                ('plastic_kg', models.DecimalField(decimal_places=3, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ('co2_saved_kg', models.DecimalField(decimal_places=3, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ('water_saved_liters', models.DecimalField(decimal_places=2, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ('items_count', models.PositiveIntegerField(default=0, help_text='Units sold (sales) or items made (production)')),
                ('people_engaged', models.PositiveIntegerField(default=0)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='impact_entries', to=settings.AUTH_USER_MODEL)),
                ('order_item', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='impact_entry', to='orders.orderitem')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='impact_entries', to='products.product')),
                ('zone', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='impact_entries', to='impact.collectionzone')),
            ],
            options={
                'verbose_name_plural': 'Impact Entries',
                'ordering': ['-date', '-created_at'],
                'indexes': [models.Index(fields=['source', 'date'], name='impact_entry_source_date_idx')],
            },
        ),
    ]
