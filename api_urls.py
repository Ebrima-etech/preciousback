from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.views import ProductViewSet, CategoryViewSet, ProductReviewViewSet
from orders.views import OrderViewSet, CartViewSet
from accounts.views import AuthViewSet, UserViewSet, AddressViewSet
from payments.views import PaymentViewSet

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

urlpatterns = [
    path('', include(router.urls)),
]
