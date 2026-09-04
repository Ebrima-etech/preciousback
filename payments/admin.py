from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order__id', 'transaction_id']
    readonly_fields = ['transaction_id', 'created_at', 'updated_at']
    fieldsets = (
        ('Order', {'fields': ('order',)}),
        ('Payment Details', {'fields': ('amount', 'status', 'payment_method')}),
        ('Transaction', {'fields': ('transaction_id',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
