from rest_framework import serializers
from decimal import Decimal
from .models import Order, OrderItem, Cart, CartItem, generate_order_number
from products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    order_number = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'order_number', 'user_id', 'user_email', 'total_price', 'status', 'items', 'created_at', 'updated_at',
                  'payment_method', 'shipping_country', 'shipping_country_name', 'is_international', 'shipping_name',
                  'shipping_phone', 'shipping_email', 'delivery_location', 'shipping_address_line1', 'shipping_house_number',
                  'shipping_address_line2', 'shipping_city', 'shipping_region', 'shipping_postal_code', 'shipping_po_box',
                  'delivery_fee', 'shipping_address']
        read_only_fields = ['id', 'created_at', 'updated_at', 'payment_method', 'shipping_country', 'shipping_name',
                            'shipping_phone', 'shipping_email', 'delivery_location', 'shipping_address_line1',
                            'shipping_house_number', 'shipping_address_line2', 'shipping_city', 'shipping_region',
                            'shipping_postal_code', 'shipping_po_box', 'delivery_fee']

    shipping_country_name = serializers.SerializerMethodField()
    is_international = serializers.BooleanField(read_only=True)
    shipping_address = serializers.SerializerMethodField()

    def get_shipping_country_name(self, obj):
        from .countries import country_name
        return country_name(obj.shipping_country)

    def get_shipping_address(self, obj):
        return obj.shipping_address_lines()

    def get_order_number(self, obj):
        # Return order_number if it exists, otherwise generate random one
        if hasattr(obj, 'order_number') and obj.order_number:
            return obj.order_number
        return generate_order_number()

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
