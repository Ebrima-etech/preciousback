import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('impact', '0007_volunteeropportunity'),
        ('cms', '0006_teammember_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='VolunteerApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(blank=True, max_length=40)),
                ('location', models.CharField(blank=True, help_text='Town / area', max_length=120)),
                ('interests', models.JSONField(blank=True, default=list, help_text='Volunteer opportunity titles they picked')),
                ('availability', models.CharField(choices=[('weekdays', 'Weekdays'), ('weekends', 'Weekends'), ('evenings', 'Evenings'), ('flexible', 'Flexible')], default='flexible', max_length=20)),
                ('skills', models.TextField(blank=True, help_text='Skills or experience')),
                ('motivation', models.TextField(help_text='Why they want to volunteer')),
                ('how_heard', models.CharField(blank=True, max_length=120)),
                ('status', models.CharField(choices=[('new', 'New'), ('contacted', 'Contacted'), ('approved', 'Approved'), ('declined', 'Declined')], default='new', max_length=20)),
                ('admin_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('team_member', models.ForeignKey(blank=True, help_text='Set when the applicant was added to the team as a volunteer', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='volunteer_applications', to='cms.teammember')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
