from rest_framework import serializers
from .models import Product, Category, ProductReview, Voucher, Discount, Location, ProductImage

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category', 'category_name', 'image', 'stock', 'rating', 'reviews_count', 'is_active', 'delivery_prices', 'created_at']
        read_only_fields = ['id', 'created_at', 'rating', 'reviews_count']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            representation['image'] = instance.image.url
        return representation

class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_url', 'alt_text', 'order']
        read_only_fields = ['id']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

class ProductDetailSerializer(ProductSerializer):
    reviews = serializers.SerializerMethodField()
    product_images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ProductSerializer.Meta.fields + ['reviews', 'product_images', 'updated_at']

    def get_reviews(self, obj):
        reviews = obj.product_reviews.all()
        return ProductReviewSerializer(reviews, many=True).data

    def get_product_images(self, obj):
        images = obj.images.all()
        return ProductImageSerializer(images, many=True).data

class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'user_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']


class VoucherSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Voucher
        fields = ['id', 'code', 'discount_percentage', 'description', 'max_uses', 'times_used', 'is_active', 'valid_from', 'valid_until', 'is_valid', 'created_at']
        read_only_fields = ['id', 'times_used', 'created_at']

    def get_is_valid(self, obj):
        return obj.is_valid()


class DiscountSerializer(serializers.ModelSerializer):
    product_names = serializers.SerializerMethodField()
    category_names = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Discount
        fields = ['id', 'name', 'description', 'discount_type', 'discount_value', 'products', 'product_names', 'categories', 'category_names', 'is_active', 'valid_from', 'valid_until', 'is_valid', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_product_names(self, obj):
        return [p.name for p in obj.products.all()]

    def get_category_names(self, obj):
        return [c.name for c in obj.categories.all()]

    def get_is_valid(self, obj):
        return obj.is_valid()
