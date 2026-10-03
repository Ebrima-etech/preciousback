from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from orders.models import Order, OrderItem
from products.models import Category, Product
from .models import ImpactEntry, ImpactMetric
from .services import compute_summary, rebuild_sales_impact


class ImpactTestBase(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user('customer@example.com', 'pass12345', first_name='Cus', last_name='Tomer')
        self.staff = User.objects.create_user('staff@example.com', 'pass12345', first_name='Sta', last_name='Ff', is_staff=True)
        category = Category.objects.create(name='Furniture')
        self.product = Product.objects.create(
            name='Recycled Stool', description='Stool', price=Decimal('500'), category=category, stock=10,
            plastic_type='HDPE', plastic_recycled_kg=Decimal('2.5'), co2_saved_kg=Decimal('4'),
            water_saved_liters=Decimal('10'),
        )
        self.client = APIClient()

    def make_order(self, status='payment_pending', quantity=2):
        order = Order.objects.create(user=self.customer, total_price=Decimal('1000'), status=status)
        OrderItem.objects.create(order=order, product=self.product, quantity=quantity, price=Decimal('500'))
        return order


class SalesTrackingTests(ImpactTestBase):
    def test_confirming_order_records_sale_impact(self):
        order = self.make_order()
        self.assertEqual(ImpactEntry.objects.count(), 0)

        order.status = 'processing'
        order.save()

        entry = ImpactEntry.objects.get()
        self.assertEqual(entry.source, 'sale')
        self.assertEqual(entry.items_count, 2)
        self.assertEqual(entry.plastic_kg, Decimal('5.000'))
        self.assertEqual(entry.co2_saved_kg, Decimal('8.000'))
        self.assertEqual(entry.plastic_type, 'HDPE')

    def test_status_changes_do_not_duplicate_entries(self):
        order = self.make_order()
        for status in ('processing', 'shipped', 'delivered'):
            order.status = status
            order.save()
        self.assertEqual(ImpactEntry.objects.count(), 1)

    def test_cancelling_order_removes_sale_impact(self):
        order = self.make_order(status='payment_pending')
        order.status = 'processing'
        order.save()
        order.status = 'cancelled'
        order.save()
        self.assertEqual(ImpactEntry.objects.count(), 0)

    def test_rebuild_backfills_and_refreshes(self):
        order = self.make_order()
        Order.objects.filter(pk=order.pk).update(status='delivered')  # bypasses signals

        self.assertEqual(rebuild_sales_impact()['created'], 1)

        Product.objects.filter(pk=self.product.pk).update(plastic_recycled_kg=Decimal('3'))
        result = rebuild_sales_impact(refresh=True)
        self.assertEqual(result['updated'], 1)
        self.assertEqual(ImpactEntry.objects.get().plastic_kg, Decimal('6.000'))


class SummaryTests(ImpactTestBase):
    def test_totals_do_not_double_count_collected_and_sold_plastic(self):
        order = self.make_order()
        order.status = 'processing'
        order.save()  # 5 kg in products sold
        ImpactEntry.objects.create(source='collection', plastic_kg=Decimal('20'), people_engaged=15)

        totals = compute_summary()['totals']
        self.assertEqual(totals['plastic_collected_kg'], 20.0)
        self.assertEqual(totals['plastic_in_products_sold_kg'], 5.0)
        self.assertEqual(totals['plastic_diverted_kg'], 20.0)
        self.assertEqual(totals['products_sold'], 2)
        self.assertEqual(totals['people_engaged'], 15)
        self.assertEqual(totals['bottles_equivalent'], 1000)

    def test_public_summary_hides_sales_breakdown(self):
        response = self.client.get('/api/impact/summary/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('top_products', response.data)

        self.client.force_authenticate(self.staff)
        response = self.client.get('/api/impact/summary/')
        self.assertIn('top_products', response.data)
        self.assertEqual(response.data['catalog']['products_with_impact'], 1)

    def test_summary_rejects_bad_dates(self):
        response = self.client.get('/api/impact/summary/?start=not-a-date')
        self.assertEqual(response.status_code, 400)


class EntryApiTests(ImpactTestBase):
    def test_only_staff_can_use_the_log(self):
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get('/api/impact/entries/').status_code, 403)

        self.client.force_authenticate(self.staff)
        response = self.client.post('/api/impact/entries/', {'source': 'collection', 'plastic_kg': '12.5', 'date': '2026-09-01'})
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(ImpactEntry.objects.get().created_by, self.staff)

    def test_manual_sale_fills_impact_from_product(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post('/api/impact/entries/', {'source': 'sale', 'product': self.product.id, 'items_count': 4})
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(ImpactEntry.objects.get().plastic_kg, Decimal('10.000'))

    def test_automatic_entries_are_read_only(self):
        order = self.make_order()
        order.status = 'processing'
        order.save()
        entry = ImpactEntry.objects.get()

        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.delete(f'/api/impact/entries/{entry.id}/').status_code, 400)
        self.assertEqual(self.client.patch(f'/api/impact/entries/{entry.id}/', {'plastic_kg': '1'}).status_code, 400)


class MetricApiTests(ImpactTestBase):
    def test_metrics_are_public_but_only_staff_can_edit(self):
        ImpactMetric.objects.create(label='Visible', value='10')
        ImpactMetric.objects.create(label='Hidden', value='5', is_active=False)

        response = self.client.get('/api/impact/metrics/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([m['label'] for m in response.data], ['Visible'])

        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.post('/api/impact/metrics/', {'label': 'X', 'value': '1'}).status_code, 403)

    def test_auto_value_uses_live_totals(self):
        ImpactEntry.objects.create(source='collection', plastic_kg=Decimal('1234.5'))
        ImpactMetric.objects.create(label='Plastic diverted', auto_value='plastic_diverted_kg')

        response = self.client.get('/api/impact/metrics/')
        self.assertEqual(response.data[0]['display_value'], '1,234.5 kg')


class ProductImpactApiTests(ImpactTestBase):
    def test_product_detail_includes_impact(self):
        response = self.client.get(f'/api/products/{self.product.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['plastic_type'], 'HDPE')
        self.assertEqual(response.data['bottles_equivalent'], 125)
        self.assertTrue(response.data['has_impact'])
        self.assertEqual(response.data['lifetime_impact']['units_sold'], 0)
