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


class CustomerImpactTests(ImpactTestBase):
    def confirm(self, order):
        order.refresh_from_db()  # pick up the order number set by the post_save signal
        order.status = 'delivered'
        order.save()

    def test_customer_sees_own_confirmed_impact(self):
        self.confirm(self.make_order(quantity=2))  # 5 kg, 8 kg CO2
        self.make_order(quantity=1)  # not confirmed yet

        self.client.force_authenticate(self.customer)
        data = self.client.get('/api/impact/me/').data

        self.assertTrue(data['has_impact'])
        self.assertEqual(data['totals']['plastic_kg'], 5.0)
        self.assertEqual(data['totals']['products_bought'], 2)
        self.assertEqual(data['totals']['orders'], 1)
        self.assertEqual(data['totals']['bottles_equivalent'], 250)
        self.assertEqual(data['level']['key'], 'guardian')
        self.assertEqual(data['next_level']['key'], 'hero')
        self.assertEqual(data['pending']['plastic_kg'], 2.5)
        self.assertEqual(data['rank']['position'], 1)
        earned = {b['key'] for b in data['badges'] if b['earned']}
        self.assertEqual(earned, {'first_step', 'one_kg', 'bottles_100'})
        self.assertEqual(data['products'][0]['units'], 2)

    def test_other_customers_purchases_are_not_included(self):
        other = User.objects.create_user('other@example.com', 'pass12345', first_name='Oth', last_name='Er')
        order = Order.objects.create(user=other, total_price=Decimal('500'), status='payment_pending')
        OrderItem.objects.create(order=order, product=self.product, quantity=1, price=Decimal('500'))
        self.confirm(order)

        self.client.force_authenticate(self.customer)
        data = self.client.get('/api/impact/me/').data
        self.assertFalse(data['has_impact'])
        self.assertIsNone(data['rank'])
        self.assertEqual(data['community']['supporters'], 1)

    def test_requires_login(self):
        self.assertEqual(self.client.get('/api/impact/me/').status_code, 401)

    def test_share_link_shows_public_card_only(self):
        self.confirm(self.make_order(quantity=2))
        self.client.force_authenticate(self.customer)
        token = self.client.get('/api/impact/me/').data['share_token']

        public = APIClient().get(f'/api/impact/share/{token}/')
        self.assertEqual(public.status_code, 200)
        self.assertEqual(public.data['display_name'], 'Cus T.')
        self.assertEqual(public.data['totals']['plastic_kg'], 5.0)
        self.assertNotIn('share_token', public.data)
        self.assertNotIn('products', public.data)
        self.assertNotIn('pending', public.data)

    def test_tampered_share_link_is_rejected(self):
        self.client.force_authenticate(self.customer)
        token = self.client.get('/api/impact/me/').data['share_token']
        forged = f'{self.staff.pk}.{token.split(".", 1)[1]}'
        self.assertEqual(APIClient().get(f'/api/impact/share/{forged}/').status_code, 404)


class CustomerCommunityStatsTests(ImpactTestBase):
    def test_public_summary_includes_anonymous_customer_stats(self):
        order = self.make_order(quantity=2)  # 5 kg -> Ocean Guardian
        order.refresh_from_db()
        order.status = 'delivered'
        order.save()

        data = self.client.get('/api/impact/summary/').data['customers']
        self.assertEqual(data['supporters'], 1)
        self.assertEqual(data['plastic_kg'], 5.0)
        self.assertEqual(data['average_plastic_kg'], 5.0)
        levels = {lvl['key']: lvl['count'] for lvl in data['levels']}
        self.assertEqual(levels['guardian'], 1)
        self.assertEqual(sum(levels.values()), 1)
        self.assertNotIn('customer@example.com', str(data))


class SponsorshipTests(ImpactTestBase):
    payload = {
        'sponsor_type': 'individual', 'sponsor_name': 'Fatou Ceesay', 'sponsor_email': 'fatou@example.com',
        'sponsor_phone': '+220 700 0000', 'item_type': 'School Desk', 'items_count': 3, 'message': 'For Kartong LBS',
    }

    def test_public_can_submit_and_amount_is_calculated_on_server(self):
        response = self.client.post('/api/impact/sponsorship/', {**self.payload, 'amount': '1'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(response.data['reference'].startswith('SP-'))
        self.assertEqual(Decimal(response.data['amount']), Decimal('450'))
        self.assertEqual(response.data['currency'], 'USD')
        self.assertEqual(response.data['status'], 'pending')

    def test_submit_works_with_a_stale_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer not-a-real-token')
        self.assertEqual(self.client.post('/api/impact/sponsorship/', self.payload, format='json').status_code, 201)

    def test_organization_requires_name(self):
        response = self.client.post('/api/impact/sponsorship/', {**self.payload, 'sponsor_type': 'organization'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('organization_name', response.data)

    def test_rejects_unknown_item_and_bad_count(self):
        self.assertEqual(self.client.post('/api/impact/sponsorship/', {**self.payload, 'item_type': 'Yacht'}, format='json').status_code, 400)
        self.assertEqual(self.client.post('/api/impact/sponsorship/', {**self.payload, 'items_count': 0}, format='json').status_code, 400)

    def test_only_staff_can_list_and_update(self):
        self.client.post('/api/impact/sponsorship/', self.payload, format='json')
        self.assertEqual(self.client.get('/api/impact/sponsorship/').status_code, 401)
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get('/api/impact/sponsorship/').status_code, 403)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get('/api/impact/sponsorship/').data['count'], 1)

    def test_options_are_public(self):
        response = self.client.get('/api/impact/sponsorship/options/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['items'][0]['item_type'], 'School Desk')
        self.assertEqual(response.data['items'][0]['unit_price'], 150.0)

    def test_delivered_sponsorship_is_added_to_impact_log(self):
        sponsorship_id = self.client.post('/api/impact/sponsorship/', self.payload, format='json').data['id']
        self.client.force_authenticate(self.staff)

        self.client.patch(f'/api/impact/sponsorship/{sponsorship_id}/', {'status': 'delivered'}, format='json')
        entry = ImpactEntry.objects.get(sponsorship_id=sponsorship_id)
        self.assertEqual(entry.items_count, 3)
        self.assertEqual(entry.plastic_kg, Decimal('15.000'))

        self.client.patch(f'/api/impact/sponsorship/{sponsorship_id}/', {'status': 'cancelled'}, format='json')
        self.assertFalse(ImpactEntry.objects.filter(sponsorship_id=sponsorship_id).exists())
