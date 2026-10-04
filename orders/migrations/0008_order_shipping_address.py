from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_fill_blank_order_numbers'),
    ]

    operations = [
        migrations.AddField(model_name='order', name='shipping_country', field=models.CharField(default='GM', max_length=2)),
        migrations.AddField(model_name='order', name='shipping_name', field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name='order', name='shipping_phone', field=models.CharField(blank=True, max_length=40)),
        migrations.AddField(model_name='order', name='shipping_email', field=models.EmailField(blank=True, max_length=254)),
        migrations.AddField(model_name='order', name='delivery_location', field=models.CharField(blank=True, help_text='Gambian delivery area', max_length=255)),
        migrations.AddField(model_name='order', name='shipping_address_line1', field=models.CharField(blank=True, help_text='Street address', max_length=255)),
        migrations.AddField(model_name='order', name='shipping_house_number', field=models.CharField(blank=True, help_text='House / apartment / unit', max_length=50)),
        migrations.AddField(model_name='order', name='shipping_address_line2', field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name='order', name='shipping_city', field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name='order', name='shipping_region', field=models.CharField(blank=True, help_text='State / province / region', max_length=120)),
        migrations.AddField(model_name='order', name='shipping_postal_code', field=models.CharField(blank=True, max_length=20)),
        migrations.AddField(model_name='order', name='shipping_po_box', field=models.CharField(blank=True, max_length=50)),
        migrations.AddField(model_name='order', name='delivery_fee', field=models.DecimalField(decimal_places=2, default=0, max_digits=10)),
    ]
