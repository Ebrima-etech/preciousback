from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order__id', 'stripe_payment_intent', 'transaction_id']
    readonly_fields = ['stripe_payment_intent', 'transaction_id', 'created_at', 'updated_at']
    fieldsets = (
        ('Order', {'fields': ('order',)}),
        ('Payment Details', {'fields': ('amount', 'status', 'payment_method')}),
        ('Stripe', {'fields': ('stripe_payment_intent', 'transaction_id')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
