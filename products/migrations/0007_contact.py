# Generated migration for Contact model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_location_default_delivery_price'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254)),
                ('phone_number', models.CharField(blank=True, max_length=20)),
                ('subject', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('status', models.CharField(choices=[('new', 'New'), ('read', 'Read'), ('replied', 'Replied'), ('resolved', 'Resolved')], default='new', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Contacts',
                'ordering': ['-created_at'],
            },
        ),
    ]
