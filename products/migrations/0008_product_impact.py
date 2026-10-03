import django.core.validators
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


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_contact'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='plastic_type',
            field=models.CharField(blank=True, choices=PLASTIC_TYPE_CHOICES, max_length=20),
        ),
        migrations.AddField(
            model_name='product',
            name='plastic_recycled_kg',
            field=models.DecimalField(decimal_places=3, default=0, help_text='Kg of recycled plastic used to make one unit', max_digits=10, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='product',
            name='co2_saved_kg',
            field=models.DecimalField(decimal_places=3, default=0, help_text='Kg of CO2e avoided per unit compared to a virgin-material equivalent', max_digits=10, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='product',
            name='water_saved_liters',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Liters of water saved per unit compared to a virgin-material equivalent', max_digits=10, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='product',
            name='plastic_source',
            field=models.CharField(blank=True, help_text="Where the plastic was collected, e.g. 'Gunjur beach cleanups'", max_length=255),
        ),
        migrations.AddField(
            model_name='product',
            name='impact_story',
            field=models.TextField(blank=True, help_text="Short story about this product's impact"),
        ),
    ]
