from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import F
import logging
from .models import Order, Cart, CartItem, OrderItem
from .serializers import OrderSerializer, CartSerializer, CartItemSerializer
from products.models import Product
from payments.modempay import create_payment_intent, ModemPayError

logger = logging.getLogger(__name__)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def create_payment(self, request):
        """Create a payment intent for Wave checkout"""
        try:
            data = request.data

            # Validate required fields
            required_fields = ['total_amount', 'deliver_to', 'contact_number', 'delivery_location', 'items', 'return_url', 'cancel_url']
            for field in required_fields:
                if field not in data:
                    return Response(
                        {'error': f'Missing required field: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Create order with transaction
            with transaction.atomic():
                # Create order
                order = Order.objects.create(
                    user=request.user,
                    total_price=data['total_amount'],
                    status='payment_pending',
                    payment_method='wave',
                    notes=f"Deliver to: {data['deliver_to']}\nPhone: {data['contact_number']}\nLocation: {data['delivery_location']}"
                )

                # Create order items
                for item in data['items']:
                    OrderItem.objects.create(
                        order=order,
                        product_id=item['product_id'],
                        quantity=item['quantity'],
                        price=item['price']
                    )

                # Create payment intent with ModemPay
                try:
                    intent = create_payment_intent(
                        amount=float(data['total_amount']),
                        currency='GMD',
                        customer_email=request.user.email or '',
                        customer_name=request.user.first_name or request.user.username,
                        customer_phone=data['contact_number'],
                        return_url=data['return_url'],
                        cancel_url=data['cancel_url'],
                        metadata={'order_id': str(order.id)}
                    )
                except ModemPayError as e:
                    logger.error(f'ModemPay error for order {order.id}: {str(e)}')
                    order.delete()
                    return Response(
                        {'error': str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Store payment reference
                order.payment_reference = intent.get('payment_intent_id', '')
                order.save()

                # Clear user's cart
                try:
                    cart = Cart.objects.get(user=request.user)
                    cart.items.all().delete()
                except Cart.DoesNotExist:
                    pass

                return Response({
                    'order_id': str(order.id),
                    'checkout_url': intent['payment_link']
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f'Payment creation error: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Failed to create payment'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        try:
            try:
                cart = Cart.objects.get(user=request.user)
            except Cart.DoesNotExist:
                cart = Cart.objects.create(user=request.user)
            serializer = CartSerializer(cart)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f'Cart list error: {str(e)}', exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        try:
            try:
                cart = Cart.objects.get(user=request.user)
            except Cart.DoesNotExist:
                cart = Cart.objects.create(user=request.user)

            serializer = CartItemSerializer(data=request.data)
            if serializer.is_valid():
                product_id = serializer.validated_data['product_id']
                quantity = serializer.validated_data.get('quantity', 1)

                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product_id=product_id,
                    defaults={'quantity': quantity}
                )
                if not created:
                    cart_item.quantity += quantity
                    cart_item.save()

                return Response(CartSerializer(cart).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Add item error: {str(e)}', exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['patch'])
    def update_item(self, request):
        try:
            cart_item_id = request.data.get('cart_item_id')
            quantity = request.data.get('quantity')

            cart_item = CartItem.objects.get(id=cart_item_id, cart__user=request.user)
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()

            cart = Cart.objects.get(user=request.user)
            return Response(CartSerializer(cart).data)
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f'Update item error: {str(e)}', exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['delete'])
    def remove_item(self, request):
        try:
            cart_item_id = request.data.get('cart_item_id')
            CartItem.objects.get(id=cart_item_id, cart__user=request.user).delete()
            cart = Cart.objects.get(user=request.user)
            return Response(CartSerializer(cart).data)
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f'Remove item error: {str(e)}', exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
            return Response({'success': 'Cart cleared'}, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({'success': 'Cart cleared'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f'Clear cart error: {str(e)}', exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
