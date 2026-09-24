# Generated migration for EventRegistration why_join field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('impact', '0002_alter_eventregistration_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventregistration',
            name='why_join',
            field=models.TextField(default='', help_text='Why do you want to join this event?'),
            preserve_default=False,
        ),
    ]
