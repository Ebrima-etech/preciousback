from django.contrib import admin
from .models import Category, Product, ProductReview

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'rating', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['rating', 'reviews_count']
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'description', 'category')}),
        ('Pricing & Inventory', {'fields': ('price', 'stock')}),
        ('Media', {'fields': ('image',)}),
        ('Impact (per unit)', {'fields': ('plastic_type', 'plastic_recycled_kg', 'co2_saved_kg', 'water_saved_liters', 'plastic_source', 'impact_story')}),
        ('Rating', {'fields': ('rating', 'reviews_count')}),
        ('Status', {'fields': ('is_active',)}),
    )

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__email', 'comment']
    readonly_fields = ['created_at']
