from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.views import ProductViewSet, CategoryViewSet, ProductReviewViewSet
from orders.views import OrderViewSet, CartViewSet
from accounts.views import AuthViewSet, UserViewSet, AddressViewSet
from payments.views import PaymentViewSet
from cms.views import (
    PageViewSet, TestimonialViewSet, BannerViewSet, FAQViewSet,
    BlogPostViewSet, ServiceViewSet, ContactInformationViewSet,
    NewsletterViewSet, ContactMessageViewSet, FeatureViewSet, SiteSettingsViewSet
)

router = DefaultRouter()

# Products
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'reviews', ProductReviewViewSet, basename='review')

# Orders
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'cart', CartViewSet, basename='cart')

# Accounts & Auth
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'users', UserViewSet, basename='user')
router.register(r'addresses', AddressViewSet, basename='address')

# Payments
router.register(r'payments', PaymentViewSet, basename='payment')

# CMS
router.register(r'pages', PageViewSet, basename='page')
router.register(r'testimonials', TestimonialViewSet, basename='testimonial')
router.register(r'banners', BannerViewSet, basename='banner')
router.register(r'faqs', FAQViewSet, basename='faq')
router.register(r'blog', BlogPostViewSet, basename='blog')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'contact-info', ContactInformationViewSet, basename='contact-info')
router.register(r'newsletter', NewsletterViewSet, basename='newsletter')
router.register(r'contact-messages', ContactMessageViewSet, basename='contact-message')
router.register(r'features', FeatureViewSet, basename='feature')
router.register(r'site-settings', SiteSettingsViewSet, basename='site-settings')

urlpatterns = [
    path('', include(router.urls)),
]
