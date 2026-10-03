from django.contrib import admin
from .models import ImpactMetric, ImpactEntry, CollectionZone, Event, NewsletterSubscription, BulkRFQ, Sponsorship
from .constants import SPONSORSHIP_ITEMS


@admin.register(ImpactMetric)
class ImpactMetricAdmin(admin.ModelAdmin):
    list_display = ['label', 'value', 'auto_value', 'order', 'is_active', 'updated_at']
    list_editable = ['order', 'is_active']


@admin.register(ImpactEntry)
class ImpactEntryAdmin(admin.ModelAdmin):
    list_display = ['date', 'source', 'title', 'plastic_type', 'plastic_kg', 'co2_saved_kg', 'items_count', 'people_engaged']
    list_filter = ['source', 'plastic_type', 'date', 'zone']
    search_fields = ['title', 'notes', 'product__name']
    date_hierarchy = 'date'
    raw_id_fields = ['product', 'order_item', 'created_by']


admin.site.register(CollectionZone)
admin.site.register(Event)
admin.site.register(NewsletterSubscription)
admin.site.register(BulkRFQ)


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = ['reference', 'sponsor_name', 'organization_name', 'items_count', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'sponsor_type', 'item_type']
    search_fields = ['reference', 'sponsor_name', 'organization_name', 'sponsor_email']
    readonly_fields = ['reference', 'amount', 'currency', 'created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        config = SPONSORSHIP_ITEMS.get(obj.item_type)
        if config:
            obj.amount = config['unit_price'] * obj.items_count
            obj.currency = config['currency']
        elif obj.amount is None:
            obj.amount = 0
        super().save_model(request, obj, form, change)
