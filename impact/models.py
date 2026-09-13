from django.db import models

class ImpactMetric(models.Model):
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)
    color_from = models.CharField(max_length=20, default="emerald-600")
    color_to = models.CharField(max_length=20, default="teal-600")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Impact Metrics"

    def __str__(self):
        return f"{self.label}: {self.value}"


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
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    product_items = models.JSONField(default=dict)
    quantity = models.IntegerField()
    custom_requirements = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.organization_name} - {self.status}"


class Sponsorship(models.Model):
    sponsor_name = models.CharField(max_length=255)
    sponsor_email = models.EmailField()
    items_count = models.IntegerField(default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    item_type = models.CharField(max_length=100, default="School Desk")
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sponsor_name} - {self.item_type}"
