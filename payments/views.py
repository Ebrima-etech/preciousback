from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Payment
from .serializers import PaymentSerializer, PaymentCreateSerializer
from orders.models import Order

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user)

    @action(detail=False, methods=['post'])
    def create_payment_intent(self, request):
        """Create a payment for an order (demo - no actual payment processing)"""
        serializer = PaymentCreateSerializer(data=request.data)
        if serializer.is_valid():
            order_id = serializer.validated_data['order_id']
            amount = serializer.validated_data['amount']

            try:
                order = Order.objects.get(id=order_id, user=request.user)
            except Order.DoesNotExist:
                return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

            # Create payment record (demo - no actual payment gateway)
            payment, created = Payment.objects.get_or_create(
                order=order,
                defaults={
                    'amount': amount,
                    'payment_method': 'card',
                    'status': 'pending'
                }
            )

            return Response({
                'payment_id': payment.id,
                'status': 'pending',
                'amount': amount,
                'message': 'Demo payment - no actual charge'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def confirm_payment(self, request, pk=None):
        """Confirm payment and mark order as processing (demo)"""
        payment = self.get_object()

        # Demo: auto-approve all payments
        payment.status = 'completed'
        payment.transaction_id = f'demo-{payment.id}'
        payment.save()

        order = payment.order
        order.status = 'processing'
        order.save()

        return Response({
            'status': 'completed',
            'payment_id': payment.id,
            'message': 'Demo payment processed successfully'
        })

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """Refund a payment (demo)"""
        payment = self.get_object()

        if payment.status != 'completed':
            return Response({'error': 'Only completed payments can be refunded'}, status=status.HTTP_400_BAD_REQUEST)

        payment.status = 'refunded'
        payment.save()

        order = payment.order
        order.status = 'cancelled'
        order.save()

        return Response({
            'status': 'refunded',
            'payment_id': payment.id,
            'message': 'Demo payment refunded'
        })
