from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Category, ProductReview
from .serializers import ProductSerializer, CategorySerializer, ProductDetailSerializer, ProductReviewSerializer
import logging

logger = logging.getLogger(__name__)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['name']

    def get_permissions(self):
        # Allow read access to all, write access only to authenticated users
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [AllowAny()]
        return [IsAuthenticated()]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'price', 'rating']
    ordering = ['-created_at']

    def get_permissions(self):
        # Allow read access to all, write access only to authenticated users
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer

    def create(self, request, *args, **kwargs):
        try:
            logger.info(f"[UPLOAD] Creating product with image: {request.FILES.get('image', 'No image')}")
            from django.core.files.storage import default_storage
            logger.info(f"[UPLOAD] Default storage backend: {default_storage.__class__.__module__}.{default_storage.__class__.__name__}")

            # Test if Cloudinary is accessible
            try:
                import cloudinary
                logger.info(f"[UPLOAD] Cloudinary config - cloud_name: {cloudinary.config().cloud_name}")
            except Exception as e:
                logger.error(f"[UPLOAD] Cloudinary config error: {str(e)}")

            response = super().create(request, *args, **kwargs)

            # Check what was saved
            if response.data.get('image'):
                logger.info(f"[UPLOAD] Product created with image URL: {response.data.get('image')}")

            return response
        except Exception as e:
            logger.error(f"[UPLOAD] Error creating product: {str(e)}", exc_info=True)
            raise

    def update(self, request, *args, **kwargs):
        try:
            logger.info(f"[UPLOAD] Updating product with image: {request.FILES.get('image', 'No image')}")
            from django.core.files.storage import default_storage
            logger.info(f"[UPLOAD] Default storage backend: {default_storage.__class__.__module__}.{default_storage.__class__.__name__}")

            # Test if Cloudinary is accessible
            try:
                import cloudinary
                logger.info(f"[UPLOAD] Cloudinary config - cloud_name: {cloudinary.config().cloud_name}")
            except Exception as e:
                logger.error(f"[UPLOAD] Cloudinary config error: {str(e)}")

            response = super().update(request, *args, **kwargs)

            # Check what was saved
            if response.data.get('image'):
                logger.info(f"[UPLOAD] Product updated with image URL: {response.data.get('image')}")

            return response
        except Exception as e:
            logger.error(f"[UPLOAD] Error updating product: {str(e)}", exc_info=True)
            raise

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

class ProductReviewViewSet(viewsets.ModelViewSet):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ['product', 'user']
    ordering = ['-created_at']
