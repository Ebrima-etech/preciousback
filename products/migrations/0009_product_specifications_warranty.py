from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_product_impact'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='specifications',
            field=models.JSONField(blank=True, default=list, help_text='List of {"label": ..., "value": ...} rows, e.g. Dimensions, Weight, Material, Colour'),
        ),
        migrations.AddField(
            model_name='product',
            name='warranty',
            field=models.CharField(blank=True, default='1-year limited warranty', max_length=120),
        ),
    ]
