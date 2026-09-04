from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import stripe
from .models import Payment
from .serializers import PaymentSerializer, PaymentCreateSerializer
from orders.models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user)

    @action(detail=False, methods=['post'])
    def create_payment_intent(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        if serializer.is_valid():
            order_id = serializer.validated_data['order_id']
            amount = serializer.validated_data['amount']

            try:
                order = Order.objects.get(id=order_id, user=request.user)
            except Order.DoesNotExist:
                return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

            try:
                intent = stripe.PaymentIntent.create(
                    amount=int(float(amount) * 100),
                    currency='usd',
                    metadata={'order_id': order_id}
                )

                payment, created = Payment.objects.get_or_create(
                    order=order,
                    defaults={
                        'amount': amount,
                        'payment_method': 'stripe',
                        'stripe_payment_intent': intent.id,
                        'status': 'pending'
                    }
                )

                return Response({
                    'client_secret': intent.client_secret,
                    'payment_id': payment.id,
                }, status=status.HTTP_200_OK)

            except stripe.error.StripeError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def confirm_payment(self, request, pk=None):
        payment = self.get_object()
        try:
            intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent)

            if intent.status == 'succeeded':
                payment.status = 'completed'
                payment.transaction_id = intent.charges.data[0].id
                payment.save()

                order = payment.order
                order.status = 'processing'
                order.save()

                return Response(PaymentSerializer(payment).data)

            elif intent.status == 'requires_action':
                return Response({'status': 'requires_action'}, status=status.HTTP_200_OK)

            else:
                payment.status = 'failed'
                payment.save()
                return Response({'status': 'failed'}, status=status.HTTP_400_BAD_REQUEST)

        except stripe.error.StripeError as e:
            payment.status = 'failed'
            payment.save()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        payment = self.get_object()

        if payment.status != 'completed':
            return Response({'error': 'Only completed payments can be refunded'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refund = stripe.Refund.create(
                charge=payment.transaction_id,
                reason='requested_by_customer'
            )

            payment.status = 'refunded'
            payment.save()

            return Response({'status': 'refunded', 'refund_id': refund.id})
