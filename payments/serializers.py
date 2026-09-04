from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'order', 'amount', 'status', 'payment_method', 'stripe_payment_intent', 'transaction_id', 'created_at']
        read_only_fields = ['id', 'created_at']

class PaymentCreateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    payment_method = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
