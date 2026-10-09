from django.db import migrations, models


def classify_existing(apps, schema_editor):
    """Sort existing team members by their role text: founders, volunteers, everyone else staff."""
    TeamMember = apps.get_model('cms', 'TeamMember')
    for member in TeamMember.objects.all():
        role = (member.role or '').lower()
        if 'founder' in role:
            member.category = 'founder'
        elif 'volunteer' in role:
            member.category = 'volunteer'
        else:
            member.category = 'staff'
        member.save(update_fields=['category'])


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0005_service_details_consultancy'),
    ]

    operations = [
        migrations.AddField(
            model_name='teammember',
            name='category',
            field=models.CharField(choices=[('founder', 'Founder'), ('staff', 'Staff'), ('volunteer', 'Volunteer')], default='staff', max_length=20),
        ),
        migrations.RunPython(classify_existing, migrations.RunPython.noop),
    ]
