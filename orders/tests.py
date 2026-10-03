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
