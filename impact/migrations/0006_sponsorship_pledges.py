import secrets
import string

import django.db.models.deletion
from django.db import migrations, models


def generate_reference():
    chars = string.ascii_uppercase + string.digits
    return 'SP-' + ''.join(secrets.choice(chars) for _ in range(8))


def backfill(apps, schema_editor):
    Sponsorship = apps.get_model('impact', 'Sponsorship')
    # Old rows used 'active'; they are unconfirmed pledges
    Sponsorship.objects.filter(status='active').update(status='pending')
    taken = set()
    for sponsorship in Sponsorship.objects.filter(reference=''):
        ref = generate_reference()
        while ref in taken:
            ref = generate_reference()
        taken.add(ref)
        Sponsorship.objects.filter(pk=sponsorship.pk).update(reference=ref)


class Migration(migrations.Migration):

    dependencies = [
        ('impact', '0005_impact_tracking'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sponsorship',
            options={'ordering': ['-created_at']},
        ),
        migrations.AddField(
            model_name='sponsorship',
            name='reference',
            field=models.CharField(blank=True, db_index=True, max_length=20),
        ),
        migrations.AddField(
            model_name='sponsorship',
            name='sponsor_type',
            field=models.CharField(choices=[('individual', 'Individual'), ('organization', 'Organization')], default='individual', max_length=20),
        ),
        migrations.AddField(
            model_name='sponsorship',
            name='organization_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='sponsorship',
            name='sponsor_phone',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='sponsorship',
            name='currency',
            field=models.CharField(default='USD', max_length=3),
        ),
        migrations.AddField(
            model_name='sponsorship',
            name='message',
            field=models.TextField(blank=True, help_text='Dedication or note from the sponsor'),
        ),
        migrations.AddField(
            model_name='sponsorship',
            name='is_anonymous',
            field=models.BooleanField(default=False, help_text="Don't mention the sponsor by name publicly"),
        ),
        migrations.AddField(
            model_name='sponsorship',
            name='admin_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='sponsorship',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='sponsorship',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('contacted', 'Contacted'), ('paid', 'Paid'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='impactentry',
            name='sponsorship',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='impact_entry', to='impact.sponsorship'),
        ),
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
