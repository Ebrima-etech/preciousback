from django.contrib import admin
from .models import Order, OrderItem, Cart, CartItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'id']
    readonly_fields = ['user', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    fieldsets = (
        ('User Information', {'fields': ('user', 'shipping_address')}),
        ('Order Details', {'fields': ('total_price', 'status', 'notes')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    list_filter = ['created_at']
    search_fields = ['order__id', 'product__name']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
    search_fields = ['user__email']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity']
    list_filter = ['created_at']
    search_fields = ['cart__user__email', 'product__name']
