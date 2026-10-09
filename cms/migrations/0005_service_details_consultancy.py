from django.db import migrations, models


def add_consultancy(apps, schema_editor):
    """Add Consultancy next to Collections, Recycling and Workshops (only if it isn't there already)."""
    Service = apps.get_model('cms', 'Service')
    if Service.objects.filter(name__icontains='consult').exists():
        return
    last = Service.objects.order_by('-order').first()
    Service.objects.create(
        name='Consultancy',
        description='Expert advice for businesses, schools and organisations on plastic waste management, '
                    'recycling programmes and circular-economy solutions.',
        details='We help you understand the plastic waste you produce and how to reduce, collect and recycle it.\n'
                'From waste audits and collection systems to staff training and recycled-product sourcing, '
                'we design practical plans that fit your organisation.',
        icon='💡',
        order=(last.order + 1) if last else 0,
        is_active=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0004_heroslide_image_alter_heroslide_image_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='details',
            field=models.TextField(blank=True, help_text='Longer text for the service detail page (one paragraph per line)'),
        ),
        migrations.RunPython(add_consultancy, migrations.RunPython.noop),
    ]
