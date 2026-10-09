from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny, BasePermission, SAFE_METHODS
from staff.access import has_any_permission, require
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Category, ProductReview, Voucher, Discount, Location, Contact
from .serializers import ProductSerializer, CategorySerializer, ProductDetailSerializer, ProductReviewSerializer, VoucherSerializer, DiscountSerializer, LocationSerializer, ContactSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.filter(is_active=True)
    serializer_class = LocationSerializer
    permission_classes = [require('edit_products', read_public=True)]
    filterset_fields = ['name', 'is_active']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        # Catalog staff also see inactive locations so they can switch them back on
        if has_any_permission(self.request.user, 'edit_products'):
            return Location.objects.all()
        return Location.objects.filter(is_active=True)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [require('edit_products', read_public=True)]
    filterset_fields = ['name']

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['created_at', 'price', 'rating']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action == 'add_review':
            return [IsAuthenticated()]
        return [require('edit_products', 'manage_inventory', read_public=True)()]

    def get_queryset(self):
        # Catalog staff also see inactive products so they can edit and re-activate them
        if has_any_permission(self.request.user, 'edit_products', 'manage_inventory'):
            return Product.objects.all()
        return Product.objects.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer


    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_review(self, request, pk=None):
        product = self.get_object()
        serializer = ProductReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        product = self.get_object()
        reviews = product.product_reviews.all()
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)

class IsReviewOwnerOrContentStaff(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user_id == request.user.id or has_any_permission(request.user, 'manage_content')


class ProductReviewViewSet(viewsets.ModelViewSet):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsReviewOwnerOrContentStaff]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    filterset_fields = ['product', 'user']
    ordering = ['-created_at']


class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    permission_classes = [require('manage_payments', 'edit_products')]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['code', 'description']
    ordering_fields = ['created_at', 'discount_percentage', 'times_used']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def use_voucher(self, request, pk=None):
        voucher = self.get_object()
        if voucher.is_valid():
            voucher.times_used += 1
            voucher.save()
            return Response({'message': 'Voucher used successfully'}, status=status.HTTP_200_OK)
        return Response({'error': 'Voucher is not valid'}, status=status.HTTP_400_BAD_REQUEST)


class DiscountViewSet(viewsets.ModelViewSet):
    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer
    permission_classes = [require('manage_payments', 'edit_products')]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'discount_type']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'discount_value']
    ordering = ['-created_at']


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'created_at']
    search_fields = ['full_name', 'email', 'subject', 'message']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_permissions(self):
        # Allow creating contacts without authentication
        if self.request.method == 'POST':
            return [AllowAny()]
        return [require('manage_community')()]
