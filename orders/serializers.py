from rest_framework import serializers
from decimal import Decimal
from .models import Order, OrderItem, Cart, CartItem
from products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user_email', 'total_price', 'status', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price', 'total_items']

    def get_total_price(self, obj):
        total = Decimal('0')
        for item in obj.items.all():
            total += item.product.price * item.quantity
        return str(total)

    def get_total_items(self, obj):
        return obj.items.count()
