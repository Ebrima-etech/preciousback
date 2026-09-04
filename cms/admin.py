from django.contrib import admin
from .models import (
    Page, Testimonial, Banner, FAQ, BlogPost, Service,
    ContactInformation, Newsletter, ContactMessage, Feature, SiteSettings
)

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_published', 'created_at']
    list_filter = ['is_published', 'created_at']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Basic Information', {'fields': ('title', 'slug', 'content')}),
        ('SEO', {'fields': ('meta_description', 'meta_keywords')}),
        ('Status', {'fields': ('is_published',)}),
    )

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'rating', 'is_featured', 'created_at']
    list_filter = ['is_featured', 'rating', 'created_at']
    search_fields = ['name', 'company', 'content']

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'banner_type', 'is_active', 'order', 'created_at']
    list_filter = ['banner_type', 'is_active', 'created_at']
    search_fields = ['title', 'content']
    ordering = ['order', '-created_at']

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'order', 'is_published', 'created_at']
    list_filter = ['category', 'is_published', 'created_at']
    search_fields = ['question', 'answer']
    ordering = ['order', '-created_at']

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'is_published', 'published_at', 'created_at']
    list_filter = ['category', 'is_published', 'published_at', 'created_at']
    search_fields = ['title', 'content', 'author']
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Basic Information', {'fields': ('title', 'slug', 'author', 'category')}),
        ('Content', {'fields': ('excerpt', 'content', 'featured_image')}),
        ('Tags', {'fields': ('tags',)}),
        ('Publishing', {'fields': ('is_published', 'published_at')}),
    )

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']

@admin.register(ContactInformation)
class ContactInformationAdmin(admin.ModelAdmin):
    list_display = ['email', 'phone', 'city', 'country']
    search_fields = ['email', 'phone', 'address']
    fieldsets = (
        ('Contact Details', {'fields': ('email', 'phone')}),
        ('Address', {'fields': ('address', 'city', 'state', 'postal_code', 'country')}),
        ('Hours & Social', {'fields': ('business_hours', 'facebook', 'twitter', 'instagram', 'linkedin')}),
    )

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_subscribed', 'subscribed_at']
    list_filter = ['is_subscribed', 'subscribed_at']
    search_fields = ['email']
    readonly_fields = ['subscribed_at']

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Sender Information', {'fields': ('name', 'email', 'phone')}),
        ('Message', {'fields': ('subject', 'message')}),
        ('Response', {'fields': ('status', 'reply')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'description']
    ordering = ['order', 'title']

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'default_currency', 'maintenance_mode']
    fieldsets = (
        ('Site Information', {'fields': ('site_name', 'tagline', 'logo', 'favicon')}),
        ('Settings', {'fields': ('default_currency', 'default_language', 'maintenance_mode')}),
        ('Analytics', {'fields': ('enable_analytics', 'analytics_code')}),
    )
