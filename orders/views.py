from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import F
import logging
from .models import Order, Cart, CartItem, OrderItem
from .serializers import OrderSerializer, CartSerializer, CartItemSerializer
from products.models import Product
from payments.modempay import create_payment_intent, ModemPayError
from staff.access import has_any_permission, require
from .checkout import international_shipping_fee, prepare_checkout
from .countries import COUNTRIES, HOME_COUNTRY

# Staff who can see every order (order handling, reporting, payments, customer management)
ORDER_READ_PERMISSIONS = ("manage_orders", "view_reports", "view_analytics", "manage_payments", "manage_users")

logger = logging.getLogger(__name__)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # Customers can view their own orders and place new ones; changing orders is for order staff
        if self.action in ('update', 'partial_update', 'destroy', 'update_status'):
            return [require('manage_orders')()]
        if self.action == 'shipping_options':
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def shipping_options(self, request):
        """Countries we ship to and the international shipping fee, for the checkout page."""
        return Response({
            'home_country': HOME_COUNTRY,
            'currency': 'GMD',
            'international_fee': float(international_shipping_fee()),
            'countries': [{'code': code, 'name': name} for code, name in sorted(COUNTRIES.items(), key=lambda c: c[1])],
        })

    def get_queryset(self):
        # Staff who work with orders see all of them; customers only see their own
        if has_any_permission(self.request.user, *ORDER_READ_PERMISSIONS):
            return Order.objects.all()
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
            prepared = prepare_checkout(data)
            if isinstance(prepared, Response):
                return prepared
            order_fields, items, total = prepared

            # Create order with transaction
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    total_price=total,
                    status='payment_pending',
                    payment_method='wave',
                    **order_fields,
                )

                for item in items:
                    OrderItem.objects.create(order=order, **item)

                # Create payment intent with ModemPay
                try:
                    intent = create_payment_intent(
                        amount=float(total),
                        currency='GMD',
                        customer_email=request.user.email or '',
                        customer_name=request.user.first_name or request.user.username,
                        customer_phone=order.shipping_phone,
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
