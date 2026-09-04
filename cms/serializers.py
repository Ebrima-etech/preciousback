from rest_framework import serializers
from .models import (
    Page, Testimonial, Banner, FAQ, BlogPost, Service,
    ContactInformation, Newsletter, ContactMessage, Feature, SiteSettings
)

class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ['id', 'title', 'slug', 'content', 'meta_description', 'meta_keywords', 'is_published', 'created_at', 'updated_at']

class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ['id', 'name', 'title', 'company', 'content', 'image', 'rating', 'is_featured', 'created_at']

class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ['id', 'title', 'content', 'image', 'button_text', 'button_link', 'banner_type', 'is_active', 'order', 'created_at']

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'category', 'order', 'is_published', 'created_at']

class BlogPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'slug', 'author', 'excerpt', 'featured_image', 'category', 'tags', 'is_published', 'published_at', 'created_at', 'updated_at']

class BlogPostDetailSerializer(BlogPostSerializer):
    class Meta:
        model = BlogPost
        fields = BlogPostSerializer.Meta.fields + ['content']

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'icon', 'image', 'order', 'is_active']

class ContactInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInformation
        fields = ['id', 'phone', 'email', 'address', 'city', 'state', 'postal_code', 'country', 'business_hours', 'facebook', 'twitter', 'instagram', 'linkedin']

class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = ['id', 'email', 'is_subscribed', 'subscribed_at']

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'phone', 'subject', 'message', 'status', 'reply', 'created_at']

class ContactMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']

class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['id', 'title', 'description', 'icon', 'order', 'is_active']

class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = ['id', 'site_name', 'tagline', 'logo', 'favicon', 'default_currency', 'default_language', 'enable_analytics', 'maintenance_mode']
