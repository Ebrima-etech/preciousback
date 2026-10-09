from django.db import migrations, models

ICON_CHOICES = [
    ('droplet', 'Water / beach'), ('tool', 'Tools / workshop'), ('book', 'Education'), ('chart', 'Fundraising / growth'),
    ('users', 'Community'), ('heart', 'Care'), ('gift', 'Donations'), ('globe', 'Environment'),
]
COLOR_CHOICES = [('blue', 'Blue'), ('emerald', 'Green'), ('purple', 'Purple'), ('orange', 'Orange'), ('rose', 'Rose'), ('teal', 'Teal')]

# The cards that were hardcoded on the Get Involved page, so nothing disappears
DEFAULTS = [
    ('Beach Cleanups', 'Join coastal collection drives', 'droplet', 'blue'),
    ('Workshops', 'Learn our recycling process', 'tool', 'emerald'),
    ('Education', 'Teach circular economy', 'book', 'purple'),
    ('Fundraising', 'Support our initiatives', 'chart', 'orange'),
]


def add_defaults(apps, schema_editor):
    VolunteerOpportunity = apps.get_model('impact', 'VolunteerOpportunity')
    if not VolunteerOpportunity.objects.exists():
        for order, (title, description, icon, color) in enumerate(DEFAULTS):
            VolunteerOpportunity.objects.create(title=title, description=description, icon=icon, color=color, order=order)


class Migration(migrations.Migration):

    dependencies = [
        ('impact', '0006_sponsorship_pledges'),
    ]

    operations = [
        migrations.CreateModel(
            name='VolunteerOpportunity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=255)),
                ('icon', models.CharField(choices=ICON_CHOICES, default='users', max_length=20)),
                ('color', models.CharField(choices=COLOR_CHOICES, default='emerald', max_length=20)),
                ('order', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['order', 'id'], 'verbose_name_plural': 'Volunteer opportunities'},
        ),
        migrations.RunPython(add_defaults, migrations.RunPython.noop),
    ]
