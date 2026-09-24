# Generated migration for Service model color fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0002_heroslide_teamember_partner'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='color_from',
            field=models.CharField(default='emerald-600', help_text='Tailwind color class for gradient start', max_length=20),
        ),
        migrations.AddField(
            model_name='service',
            name='color_to',
            field=models.CharField(default='teal-600', help_text='Tailwind color class for gradient end', max_length=20),
        ),
    ]
