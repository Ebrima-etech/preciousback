from django.db.models.signals import post_save
from django.dispatch import receiver

from .services import sync_order_impact


@receiver(post_save, sender='orders.Order')
def record_order_impact(sender, instance, **kwargs):
    """Keep sale impact entries in step with order status (covers admin edits and payment webhooks)."""
    sync_order_impact(instance)
