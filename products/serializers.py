from rest_framework import serializers
from .models import Product, Category, ProductReview

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category', 'category_name', 'image', 'stock', 'rating', 'reviews_count', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at', 'rating', 'reviews_count']

class ProductDetailSerializer(ProductSerializer):
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ProductSerializer.Meta.fields + ['reviews', 'updated_at']

    def get_reviews(self, obj):
        reviews = obj.product_reviews.all()
        return ProductReviewSerializer(reviews, many=True).data

class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'user_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']
