from django.contrib import admin
from .models import ImpactMetric, CollectionZone, Event, NewsletterSubscription, BulkRFQ, Sponsorship

admin.site.register(ImpactMetric)
admin.site.register(CollectionZone)
admin.site.register(Event)
admin.site.register(NewsletterSubscription)
admin.site.register(BulkRFQ)
admin.site.register(Sponsorship)
