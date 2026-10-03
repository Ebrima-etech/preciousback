from django.contrib import admin
from .models import ImpactMetric, ImpactEntry, CollectionZone, Event, NewsletterSubscription, BulkRFQ, Sponsorship


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
admin.site.register(Sponsorship)
