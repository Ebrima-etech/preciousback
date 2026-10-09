from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
import secrets
import string
from .constants import PLASTIC_TYPE_CHOICES, AUTO_VALUE_CHOICES, SPONSORSHIP_STATUS_CHOICES

class ImpactMetric(models.Model):
    """Headline metric shown on the public site, either typed in or pulled from live tracking."""
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=50, blank=True)
    auto_value = models.CharField(
        max_length=40, choices=AUTO_VALUE_CHOICES, blank=True,
        help_text="If set, the value is calculated from the impact log instead of typed in"
    )
    description = models.CharField(max_length=255, blank=True)
    color_from = models.CharField(max_length=20, default="emerald-600")
    color_to = models.CharField(max_length=20, default="teal-600")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Impact Metrics"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.label}: {self.auto_value or self.value}"


class ImpactEntry(models.Model):
    """One line in the business impact log. Sales are recorded automatically from orders."""
    SOURCE_SALE = 'sale'
    SOURCE_CHOICES = [
        ('sale', 'Product sale'),
        ('collection', 'Plastic collection'),
        ('production', 'Production run'),
        ('event', 'Event / workshop'),
        ('adjustment', 'Manual adjustment'),
    ]

    date = models.DateField(default=timezone.localdate)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='collection')
    title = models.CharField(max_length=255, blank=True)
    plastic_type = models.CharField(max_length=20, choices=PLASTIC_TYPE_CHOICES, blank=True)
    plastic_kg = models.DecimalField(max_digits=12, decimal_places=3, default=0, validators=[MinValueValidator(0)])
    co2_saved_kg = models.DecimalField(max_digits=12, decimal_places=3, default=0, validators=[MinValueValidator(0)])
    water_saved_liters = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    items_count = models.PositiveIntegerField(default=0, help_text="Units sold (sales) or items made (production)")
    people_engaged = models.PositiveIntegerField(default=0)
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='impact_entries')
    order_item = models.OneToOneField('orders.OrderItem', on_delete=models.CASCADE, null=True, blank=True, related_name='impact_entry')
    sponsorship = models.OneToOneField('Sponsorship', on_delete=models.CASCADE, null=True, blank=True, related_name='impact_entry')
    zone = models.ForeignKey('CollectionZone', on_delete=models.SET_NULL, null=True, blank=True, related_name='impact_entries')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='impact_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Impact Entries"
        ordering = ['-date', '-created_at']
        indexes = [models.Index(fields=['source', 'date'], name='impact_entry_source_date_idx')]

    def __str__(self):
        return f"{self.get_source_display()} {self.date}: {self.plastic_kg} kg"


class CollectionZone(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    plastics_recovered_kg = models.IntegerField(default=0)
    items_produced = models.IntegerField(default=0)
    icon = models.CharField(max_length=10, default="🏖️")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField()
    location = models.CharField(max_length=255)
    description = models.TextField()
    spots_available = models.IntegerField(default=20)
    spots_filled = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.date}"


class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations', null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    why_join = models.TextField(help_text="Why do you want to join this event?")
    is_confirmed = models.BooleanField(default=False)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'email')
        verbose_name_plural = "Event Registrations"

    def __str__(self):
        return f"{self.name} - {self.event.title}"


class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email


class BulkRFQ(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('quoted', 'Quoted'),
        ('closed', 'Closed'),
    ]

    organization_name = models.CharField(max_length=255)
    contact_person_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    product_category = models.CharField(max_length=100, blank=True)
    quantity = models.IntegerField()
    custom_requirements = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.organization_name} - {self.status}"


def generate_sponsorship_reference():
    chars = string.ascii_uppercase + string.digits
    return 'SP-' + ''.join(secrets.choice(chars) for _ in range(8))


class Sponsorship(models.Model):
    """A sponsorship pledge from the public form. Staff follow up for payment and delivery."""
    SPONSOR_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('organization', 'Organization'),
    ]

    reference = models.CharField(max_length=20, blank=True, db_index=True)
    sponsor_type = models.CharField(max_length=20, choices=SPONSOR_TYPE_CHOICES, default='individual')
    sponsor_name = models.CharField(max_length=255)
    organization_name = models.CharField(max_length=255, blank=True)
    sponsor_email = models.EmailField()
    sponsor_phone = models.CharField(max_length=30, blank=True)
    items_count = models.IntegerField(default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    item_type = models.CharField(max_length=100, default="School Desk")
    message = models.TextField(blank=True, help_text="Dedication or note from the sponsor")
    is_anonymous = models.BooleanField(default=False, help_text="Don't mention the sponsor by name publicly")
    status = models.CharField(max_length=20, choices=SPONSORSHIP_STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference or self.pk} {self.sponsor_name} - {self.items_count} x {self.item_type}"

    def save(self, *args, **kwargs):
        if not self.reference:
            ref = generate_sponsorship_reference()
            while Sponsorship.objects.filter(reference=ref).exists():
                ref = generate_sponsorship_reference()
            self.reference = ref
        super().save(*args, **kwargs)


class VolunteerOpportunity(models.Model):
    """A "Ways to volunteer" card on the Get Involved page, managed from the admin."""
    ICON_CHOICES = [
        ('droplet', 'Water / beach'),
        ('tool', 'Tools / workshop'),
        ('book', 'Education'),
        ('chart', 'Fundraising / growth'),
        ('users', 'Community'),
        ('heart', 'Care'),
        ('gift', 'Donations'),
        ('globe', 'Environment'),
    ]
    COLOR_CHOICES = [
        ('blue', 'Blue'),
        ('emerald', 'Green'),
        ('purple', 'Purple'),
        ('orange', 'Orange'),
        ('rose', 'Rose'),
        ('teal', 'Teal'),
    ]

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    icon = models.CharField(max_length=20, choices=ICON_CHOICES, default='users')
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='emerald')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name_plural = 'Volunteer opportunities'

    def __str__(self):
        return self.title
