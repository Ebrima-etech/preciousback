import json
import logging
from django.http import JsonResponse, HttpResponseForbidden
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import F
from orders.models import Order, OrderItem
from products.models import Product
from .modempay import verify_webhook_signature

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ModemPayWebhookView(View):
    """Handle ModemPay webhook notifications"""

    def post(self, request):
        # Verify signature
        signature = request.headers.get('x-modem-signature', '')

        if not verify_webhook_signature(request.body, signature):
            logger.warning('Invalid ModemPay webhook signature')
            return HttpResponseForbidden('Invalid signature')

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error('Invalid JSON in webhook payload')
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        event = body.get('event')
        payload = body.get('payload', {})

        logger.info(f'ModemPay webhook received: {event}')

        if event == 'charge.succeeded':
            return self.handle_charge_succeeded(payload)
        elif event == 'charge.failed':
            return self.handle_charge_failed(payload)

        return JsonResponse({'status': 'ok'})

    def handle_charge_succeeded(self, payload):
        """Handle successful payment"""
        try:
            metadata = payload.get('metadata', {})
            order_id = metadata.get('order_id')

            if not order_id:
                logger.warning('No order_id in webhook payload')
                return JsonResponse({'status': 'ok'})

            order = Order.objects.filter(pk=order_id, status='payment_pending').first()

            if not order:
                logger.warning(f'Order {order_id} not found or not in payment_pending status')
                return JsonResponse({'status': 'ok'})

            # Update order status
            order.status = 'processing'
            order.save()

            # Deduct stock
            if not order.stock_deducted:
                for item in order.items.all():
                    Product.objects.filter(id=item.product_id).update(
                        stock=F('stock') - item.quantity
                    )
                order.stock_deducted = True
                order.save()

            logger.info(f'Order {order_id} payment confirmed and processed')
            return JsonResponse({'status': 'ok'})

        except Exception as e:
            logger.error(f'Error handling charge.succeeded: {str(e)}', exc_info=True)
            return JsonResponse({'status': 'ok'})  # Still return OK to prevent retries

    def handle_charge_failed(self, payload):
        """Handle failed payment"""
        try:
            metadata = payload.get('metadata', {})
            order_id = metadata.get('order_id')

            if not order_id:
                return JsonResponse({'status': 'ok'})

            order = Order.objects.filter(pk=order_id, status='payment_pending').first()

            if order:
                order.status = 'cancelled'
                order.save()
                logger.info(f'Order {order_id} payment failed, order cancelled')

            return JsonResponse({'status': 'ok'})

        except Exception as e:
            logger.error(f'Error handling charge.failed: {str(e)}', exc_info=True)
            return JsonResponse({'status': 'ok'})
