from rest_framework import serializers
from .models import ImpactMetric, CollectionZone, Event, EventRegistration, NewsletterSubscription, BulkRFQ, Sponsorship

class ImpactMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImpactMetric
        fields = ['id', 'label', 'value', 'description', 'color_from', 'color_to']

class CollectionZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionZone
        fields = ['id', 'name', 'location', 'latitude', 'longitude', 'plastics_recovered_kg', 'items_produced', 'icon']

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'title', 'date', 'location', 'description', 'spots_available', 'spots_filled']

class EventRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRegistration
        fields = ['id', 'name', 'email', 'phone', 'is_confirmed', 'registered_at']
        read_only_fields = ['id', 'is_confirmed', 'registered_at']

class NewsletterSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscription
        fields = ['email']

class BulkRFQSerializer(serializers.ModelSerializer):
    class Meta:
        model = BulkRFQ
        fields = ['id', 'organization_name', 'contact_email', 'contact_phone', 'product_items', 'quantity', 'custom_requirements', 'status']

class SponsorshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sponsorship
        fields = ['id', 'sponsor_name', 'sponsor_email', 'items_count', 'amount', 'item_type', 'status']
