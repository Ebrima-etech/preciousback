from decimal import Decimal

from django.test import TestCase

from accounts.models import User
from .models import Order


class OrderNumberTests(TestCase):
    def test_saving_again_keeps_order_number_and_next_order_succeeds(self):
        user = User.objects.create_user('buyer@example.com', 'pass12345', first_name='Buy', last_name='Er')

        first = Order.objects.create(user=user, total_price=Decimal('100'), status='payment_pending')
        self.assertTrue(first.order_number.startswith('PPG'))

        # create_payment saves the same instance again after creating it
        first.payment_reference = 'pi_123'
        first.save()
        first.refresh_from_db()
        self.assertTrue(first.order_number.startswith('PPG'))

        second = Order.objects.create(user=user, total_price=Decimal('50'), status='payment_pending')
        self.assertNotEqual(first.order_number, second.order_number)


class CheckoutTests(TestCase):
    def setUp(self):
        from unittest import mock
        from rest_framework.test import APIClient
        from products.models import Category, Location, Product

        self.client = APIClient()
        self.user = User.objects.create_user('buyer2@example.com', 'pass12345', first_name='Bu', last_name='Yer')
        self.client.force_authenticate(self.user)
        category = Category.objects.create(name='Furniture')
        self.brikama = Location.objects.create(name='Brikama')
        self.banjul = Location.objects.create(name='Banjul')
        self.product = Product.objects.create(
            name='Stool', description='d', price=Decimal('500'), category=category, stock=10,
            delivery_prices={str(self.brikama.id): '150'},
        )
        patcher = mock.patch('orders.views.create_payment_intent', return_value={'payment_intent_id': 'pi_1', 'payment_link': 'https://pay.example/1'})
        self.intent = patcher.start()
        self.addCleanup(patcher.stop)

    def base(self, **extra):
        return {
            'items': [{'product_id': self.product.id, 'quantity': 2, 'price': 1}],
            'return_url': 'https://shop.example/ok', 'cancel_url': 'https://shop.example/cancel',
            'deliver_to': 'Awa Jallow', 'contact_number': '+44 7700 900000', **extra,
        }

    def test_gambian_checkout_is_priced_on_the_server(self):
        # 2 x D500 + D150 delivery to Brikama (charged once per product, as the checkout page shows)
        response = self.client.post('/api/orders/create_payment/', self.base(
            delivery_location='Brikama', total_amount='1150', delivery_fee='999', contact_number='+220 7000000',
        ), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        order = Order.objects.get()
        self.assertEqual(order.shipping_country, 'GM')
        self.assertEqual(order.delivery_location, 'Brikama')
        self.assertEqual(order.delivery_fee, Decimal('150'))
        self.assertEqual(order.total_price, Decimal('1150'))
        self.assertEqual(order.items.get().price, Decimal('500'))  # client sent 1
        self.assertEqual(self.intent.call_args.kwargs['amount'], 1150.0)
        self.assertIn('Location: Brikama', order.notes)

    def test_tampered_or_stale_total_is_refused(self):
        response = self.client.post('/api/orders/create_payment/', self.base(
            delivery_location='Brikama', total_amount='1',
        ), format='json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['total'], 1150.0)
        self.assertFalse(Order.objects.exists())

    def test_product_without_a_price_for_the_location_delivers_free(self):
        response = self.client.post('/api/orders/create_payment/', self.base(delivery_location='Banjul', total_amount='1000'), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Order.objects.get().delivery_fee, Decimal('0'))

    def test_unknown_gambian_location_is_rejected(self):
        response = self.client.post('/api/orders/create_payment/', self.base(delivery_location='Atlantis'), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('delivery_location', response.data)

    def test_international_checkout_requires_a_postal_address(self):
        response = self.client.post('/api/orders/create_payment/', self.base(country='GB'), format='json')
        self.assertEqual(response.status_code, 400)
        for field in ('email', 'address_line1', 'city', 'postal_code'):
            self.assertIn(field, response.data)

    def test_international_checkout_is_priced_on_the_server(self):
        response = self.client.post('/api/orders/create_payment/', self.base(
            country='GB', email='awa@example.com', address_line1='10 Downing Street', house_number='Flat 2',
            city='London', region='Greater London', postal_code='SW1A 2AA',
        ), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        order = Order.objects.get()
        self.assertEqual(order.shipping_country, 'GB')
        self.assertEqual(order.items.get().price, Decimal('500'))  # client sent 1
        self.assertEqual(order.total_price, Decimal('1000') + order.delivery_fee)
        self.assertEqual(self.intent.call_args.kwargs['amount'], float(order.total_price))
        self.assertIn('London', ' '.join(order.shipping_address_lines()))

    def test_po_box_can_replace_street_and_postcode(self):
        response = self.client.post('/api/orders/create_payment/', self.base(
            country='NG', email='awa@example.com', po_box='1234', city='Lagos',
        ), format='json')
        self.assertEqual(response.status_code, 201, response.data)

    def test_unknown_country_is_rejected(self):
        response = self.client.post('/api/orders/create_payment/', self.base(country='XX'), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('country', response.data)

    def test_shipping_options_are_public(self):
        from rest_framework.test import APIClient
        response = APIClient().get('/api/orders/shipping_options/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['home_country'], 'GM')
        self.assertIn('US', {c['code'] for c in response.data['countries']})
