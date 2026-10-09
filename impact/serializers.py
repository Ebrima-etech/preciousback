from decimal import Decimal
from rest_framework import serializers
from .constants import AUTO_VALUE_UNITS, SPONSORSHIP_ITEMS
from .models import ImpactMetric, ImpactEntry, CollectionZone, Event, EventRegistration, NewsletterSubscription, BulkRFQ, Sponsorship, VolunteerOpportunity, VolunteerApplication
from .services import compute_totals


def format_metric_value(key, value):
    number = f'{value:,.1f}'.rstrip('0').rstrip('.') if isinstance(value, float) else f'{value:,}'
    unit = AUTO_VALUE_UNITS.get(key)
    return f'{number} {unit}' if unit else number


class ImpactMetricSerializer(serializers.ModelSerializer):
    display_value = serializers.SerializerMethodField()

    class Meta:
        model = ImpactMetric
        fields = ['id', 'label', 'value', 'auto_value', 'display_value', 'description',
                  'color_from', 'color_to', 'order', 'is_active', 'updated_at']
        read_only_fields = ['id', 'updated_at']

    def validate(self, attrs):
        value = attrs.get('value', getattr(self.instance, 'value', ''))
        auto_value = attrs.get('auto_value', getattr(self.instance, 'auto_value', ''))
        if not value and not auto_value:
            raise serializers.ValidationError({'value': 'Enter a value or choose a live value.'})
        return attrs

    def get_display_value(self, obj):
        if not obj.auto_value:
            return obj.value
        # Compute the totals once per response, not once per metric
        totals = self.context.get('_impact_totals')
        if totals is None:
            totals = compute_totals()
            self.context['_impact_totals'] = totals
        return format_metric_value(obj.auto_value, totals.get(obj.auto_value, 0))


class ImpactEntrySerializer(serializers.ModelSerializer):
    source_label = serializers.CharField(source='get_source_display', read_only=True)
    plastic_type_label = serializers.CharField(source='get_plastic_type_display', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True, default=None)
    zone_name = serializers.CharField(source='zone.name', read_only=True, default=None)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True, default=None)
    is_automatic = serializers.SerializerMethodField()

    class Meta:
        model = ImpactEntry
        fields = ['id', 'date', 'source', 'source_label', 'title', 'plastic_type', 'plastic_type_label',
                  'plastic_kg', 'co2_saved_kg', 'water_saved_liters', 'items_count', 'people_engaged',
                  'product', 'product_name', 'zone', 'zone_name', 'notes', 'is_automatic',
                  'created_by_email', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_automatic(self, obj):
        return obj.order_item_id is not None or obj.sponsorship_id is not None

    def validate(self, attrs):
        # Offline sales: fill impact from the product when the numbers were left at zero
        product = attrs.get('product', getattr(self.instance, 'product', None))
        items = attrs.get('items_count', getattr(self.instance, 'items_count', 0))
        source = attrs.get('source', getattr(self.instance, 'source', None))
        impact_fields = ('plastic_kg', 'co2_saved_kg', 'water_saved_liters')
        if source == 'sale' and product and items and all(
            not attrs.get(f, getattr(self.instance, f, 0)) for f in impact_fields
        ):
            qty = Decimal(items)
            attrs['plastic_kg'] = product.plastic_recycled_kg * qty
            attrs['co2_saved_kg'] = product.co2_saved_kg * qty
            attrs['water_saved_liters'] = product.water_saved_liters * qty
            if not attrs.get('plastic_type'):
                attrs['plastic_type'] = product.plastic_type
        return attrs


class CollectionZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionZone
        fields = ['id', 'name', 'location', 'latitude', 'longitude', 'plastics_recovered_kg', 'items_produced', 'icon', 'active']

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'title', 'date', 'location', 'description', 'spots_available', 'spots_filled']

class EventRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRegistration
        fields = ['id', 'name', 'email', 'phone', 'why_join', 'is_confirmed', 'registered_at']
        read_only_fields = ['id', 'is_confirmed', 'registered_at']

class NewsletterSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscription
        fields = ['email']

class BulkRFQSerializer(serializers.ModelSerializer):
    class Meta:
        model = BulkRFQ
        fields = ['id', 'organization_name', 'contact_person_name', 'contact_email', 'contact_phone', 'product_category', 'quantity', 'custom_requirements', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class SponsorshipSerializer(serializers.ModelSerializer):
    """Public sponsorship form. The amount is always calculated on the server."""
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Sponsorship
        fields = ['id', 'reference', 'sponsor_type', 'sponsor_name', 'organization_name', 'sponsor_email',
                  'sponsor_phone', 'item_type', 'items_count', 'amount', 'currency', 'message', 'is_anonymous',
                  'status', 'status_label', 'created_at']
        read_only_fields = ['id', 'reference', 'amount', 'currency', 'status', 'created_at']

    def validate_item_type(self, value):
        if value not in SPONSORSHIP_ITEMS:
            raise serializers.ValidationError(f'Choose one of: {", ".join(SPONSORSHIP_ITEMS)}.')
        return value

    def validate_items_count(self, value):
        if value < 1 or value > 1000:
            raise serializers.ValidationError('Choose between 1 and 1000.')
        return value

    def validate(self, attrs):
        sponsor_type = attrs.get('sponsor_type', getattr(self.instance, 'sponsor_type', 'individual'))
        org = attrs.get('organization_name', getattr(self.instance, 'organization_name', ''))
        if sponsor_type == 'organization' and not (org or '').strip():
            raise serializers.ValidationError({'organization_name': 'Enter the organization name.'})
        item_type = attrs.get('item_type', getattr(self.instance, 'item_type', 'School Desk'))
        count = attrs.get('items_count', getattr(self.instance, 'items_count', 1))
        config = SPONSORSHIP_ITEMS.get(item_type)
        if config:
            attrs['amount'] = config['unit_price'] * count
            attrs['currency'] = config['currency']
        return attrs


class SponsorshipAdminSerializer(SponsorshipSerializer):
    """Staff view: can also update status and internal notes."""

    class Meta(SponsorshipSerializer.Meta):
        fields = SponsorshipSerializer.Meta.fields + ['admin_notes', 'updated_at']
        read_only_fields = ['id', 'reference', 'amount', 'currency', 'created_at', 'updated_at']


class VolunteerOpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = VolunteerOpportunity
        fields = ['id', 'title', 'description', 'icon', 'color', 'order', 'is_active', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class VolunteerApplicationSerializer(serializers.ModelSerializer):
    """Public "apply to volunteer" form."""
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    availability_label = serializers.CharField(source='get_availability_display', read_only=True)

    class Meta:
        model = VolunteerApplication
        fields = ['id', 'full_name', 'email', 'phone', 'location', 'interests', 'availability', 'availability_label',
                  'skills', 'motivation', 'how_heard', 'status', 'status_label', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']

    def validate_interests(self, value):
        if value in (None, ''):
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError('Choose from the list.')
        return [str(item).strip()[:100] for item in value[:12] if str(item).strip()]

    def validate_motivation(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError('Tell us a little more (at least a sentence).')
        return value.strip()


class VolunteerApplicationAdminSerializer(VolunteerApplicationSerializer):
    team_member_name = serializers.CharField(source='team_member.name', read_only=True, default=None)

    class Meta(VolunteerApplicationSerializer.Meta):
        fields = VolunteerApplicationSerializer.Meta.fields + ['admin_notes', 'team_member', 'team_member_name', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'team_member']
