from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from .models import Department, Staff


class StaffApiTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin@example.com', 'pass12345', first_name='Ad', last_name='Min', is_staff=True)
        self.customer = User.objects.create_user('customer@example.com', 'pass12345', first_name='Cus', last_name='Tomer')
        self.department = Department.objects.create(name='Production')
        self.client = APIClient()
        self.payload = {
            'first_name': 'Awa', 'last_name': 'Jallow', 'email': 'awa@example.com', 'department': self.department.id,
            'role': 'technician', 'hire_date': '2026-09-01', 'permissions': ['manage_orders'], 'salary': '5000',
        }

    def test_only_staff_can_access(self):
        self.assertEqual(self.client.get('/api/staff/staff/').status_code, 401)
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get('/api/staff/staff/').status_code, 403)
        self.assertEqual(self.client.post('/api/staff/staff/', self.payload, format='json').status_code, 403)
        self.assertEqual(self.client.get('/api/staff/departments/').status_code, 403)

    def test_create_staff_creates_account_and_returns_password(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/staff/staff/', {**self.payload, 'admin_access': True}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(response.data['temporary_password'])
        self.assertTrue(response.data['admin_access'])
        staff = Staff.objects.get()
        self.assertEqual(staff.user.first_name, 'Awa')
        self.assertTrue(staff.user.is_staff)
        self.assertTrue(staff.user.check_password(response.data['temporary_password']))

    def test_invalid_staff_data_does_not_leave_an_orphan_user(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/staff/staff/', {**self.payload, 'hire_date': ''}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email='awa@example.com').exists())

    def test_update_changes_names_and_admin_access(self):
        self.client.force_authenticate(self.admin)
        staff_id = self.client.post('/api/staff/staff/', self.payload, format='json').data['id']
        response = self.client.patch(f'/api/staff/staff/{staff_id}/', {'first_name': 'Awa-Marie', 'admin_access': True}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        user = Staff.objects.get(pk=staff_id).user
        self.assertEqual(user.first_name, 'Awa-Marie')
        self.assertTrue(user.is_staff)

    def test_deactivated_staff_cannot_log_in(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/staff/staff/', {**self.payload, 'password': 'longpassword1'}, format='json')
        self.client.post(f"/api/staff/staff/{response.data['id']}/deactivate/")
        self.client.force_authenticate(None)
        login = self.client.post('/api/auth/login/', {'email': 'awa@example.com', 'password': 'longpassword1'}, format='json')
        self.assertEqual(login.status_code, 401)

    def test_deleting_department_with_staff_returns_400(self):
        self.client.force_authenticate(self.admin)
        self.client.post('/api/staff/staff/', self.payload, format='json')
        response = self.client.delete(f'/api/staff/departments/{self.department.id}/')
        self.assertEqual(response.status_code, 400)

    def test_deleting_staff_disables_the_account(self):
        self.client.force_authenticate(self.admin)
        staff_id = self.client.post('/api/staff/staff/', {**self.payload, 'admin_access': True}, format='json').data['id']
        user_id = Staff.objects.get(pk=staff_id).user_id
        self.assertEqual(self.client.delete(f'/api/staff/staff/{staff_id}/').status_code, 204)
        user = User.objects.get(pk=user_id)
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)

    def test_existing_account_without_staff_profile_is_reused(self):
        # e.g. an account left behind by the old, failing create
        orphan = User.objects.create_user('awa@example.com', 'oldpassword', first_name='A', last_name='J')
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/staff/staff/', self.payload, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(response.data['reused_existing_account'])
        orphan.refresh_from_db()
        self.assertEqual(orphan.staff_profile.role, 'technician')
        self.assertTrue(orphan.check_password(response.data['temporary_password']))

        again = self.client.post('/api/staff/staff/', self.payload, format='json')
        self.assertEqual(again.status_code, 400)

    def test_adding_yourself_does_not_reset_your_password(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/staff/staff/', {**self.payload, 'email': 'admin@example.com'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIsNone(response.data['temporary_password'])
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('pass12345'))

    def test_make_existing_user_staff_keeps_their_password(self):
        self.client.force_authenticate(self.admin)
        payload = {k: v for k, v in self.payload.items() if k not in ('first_name', 'last_name', 'email')}
        response = self.client.post('/api/staff/staff/', {**payload, 'user_id': self.customer.id, 'admin_access': True}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIsNone(response.data['temporary_password'])
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.staff_profile.role, 'technician')
        self.assertTrue(self.customer.is_staff)
        self.assertTrue(self.customer.check_password('pass12345'))

        again = self.client.post('/api/staff/staff/', {**payload, 'user_id': self.customer.id}, format='json')
        self.assertEqual(again.status_code, 400)

    def test_candidates_lists_only_non_staff_users(self):
        self.client.force_authenticate(self.admin)
        self.client.post('/api/staff/staff/', self.payload, format='json')  # awa becomes staff
        response = self.client.get('/api/staff/staff/candidates/', {'search': 'example.com'})
        emails = {u['email'] for u in response.data}
        self.assertIn('customer@example.com', emails)
        self.assertNotIn('awa@example.com', emails)

    def test_candidates_is_staff_only(self):
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get('/api/staff/staff/candidates/').status_code, 403)


class StaffDashboardTests(TestCase):
    def setUp(self):
        from orders.models import Order, OrderItem
        from products.models import Category, Product

        self.client = APIClient()
        self.admin = User.objects.create_user('boss@example.com', 'pass12345', first_name='Bo', last_name='Ss', is_staff=True)
        self.customer = User.objects.create_user('buyer@example.com', 'pass12345', first_name='Bu', last_name='Yer')
        self.logistics = Department.objects.create(name='Logistics', budget_allocation=Decimal('1000'))
        self.driver_user = User.objects.create_user('driver@example.com', 'pass12345', first_name='Dr', last_name='Iver')
        self.driver = Staff.objects.create(user=self.driver_user, department=self.logistics, role='driver',
                                           permissions=['manage_orders'], hire_date='2026-01-01', phone_number='+220 1')
        self.tech_user = User.objects.create_user('tech@example.com', 'pass12345', first_name='Te', last_name='Ch')
        Staff.objects.create(user=self.tech_user, department=self.logistics, role='technician',
                             permissions=['manage_inventory'], hire_date='2026-01-01')
        category = Category.objects.create(name='Furniture')
        self.product = Product.objects.create(name='Stool', description='d', price=Decimal('500'), category=category, stock=2)
        self.order = Order.objects.create(user=self.customer, total_price=Decimal('500'), status='processing',
                                          notes='Deliver to: Awa\nPhone: +220 7\nLocation: Brikama')
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1, price=Decimal('500'))

    def test_customers_cannot_use_staff_dashboard(self):
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get('/api/staff/me/').status_code, 403)
        self.assertEqual(self.client.get('/api/staff/dashboard/').status_code, 403)

    def test_driver_gets_deliveries_only(self):
        self.client.force_authenticate(self.driver_user)
        me = self.client.get('/api/staff/me/').data
        self.assertFalse(me['is_admin'])
        self.assertEqual(me['modules'], ['deliveries'])

        data = self.client.get('/api/staff/dashboard/').data
        self.assertEqual(list(data['sections']), ['deliveries'])
        delivery = data['sections']['deliveries']['orders'][0]['delivery']
        self.assertEqual(delivery['location'], 'Brikama')
        self.assertNotIn('budget_allocation', data['department'])
        self.assertNotIn('phone', data['department']['members'][0])

    def test_driver_can_only_move_orders_forward_for_delivery(self):
        self.client.force_authenticate(self.driver_user)
        url = f'/api/staff/dashboard/orders/{self.order.id}/status/'
        self.assertEqual(self.client.post(url, {'status': 'cancelled'}, format='json').status_code, 403)
        self.assertEqual(self.client.post(url, {'status': 'shipped'}, format='json').status_code, 200)
        self.assertEqual(self.client.post(url, {'status': 'delivered'}, format='json').status_code, 200)

    def test_technician_updates_stock_but_not_orders(self):
        self.client.force_authenticate(self.tech_user)
        data = self.client.get('/api/staff/dashboard/').data
        self.assertEqual(list(data['sections']), ['inventory'])
        self.assertEqual(data['sections']['inventory']['low_stock'][0]['name'], 'Stool')
        self.assertEqual(self.client.post(f'/api/staff/dashboard/products/{self.product.id}/stock/', {'stock': 40}, format='json').status_code, 200)
        self.assertEqual(self.client.post(f'/api/staff/dashboard/orders/{self.order.id}/status/', {'status': 'shipped'}, format='json').status_code, 403)

    def test_admin_can_view_department_and_staff_dashboards(self):
        self.client.force_authenticate(self.admin)
        dept = self.client.get('/api/staff/dashboard/', {'department': self.logistics.id}).data
        self.assertEqual(set(dept['modules']), {'orders', 'inventory'})
        self.assertEqual(dept['department']['budget_allocation'], 1000.0)
        person = self.client.get('/api/staff/dashboard/', {'staff': self.driver.id}).data
        self.assertEqual(person['modules'], ['deliveries'])

        self.client.force_authenticate(self.driver_user)
        self.assertEqual(self.client.get('/api/staff/dashboard/', {'department': self.logistics.id}).status_code, 403)

    def test_login_flags_staff_members(self):
        response = self.client.post('/api/auth/login/', {'email': 'driver@example.com', 'password': 'pass12345'}, format='json')
        self.assertTrue(response.data['user']['is_staff_member'])


class AdminPagePermissionTests(TestCase):
    """Admin APIs follow staff permissions; full admins keep everything."""

    def setUp(self):
        from orders.models import Order
        from products.models import Category

        self.client = APIClient()
        self.admin = User.objects.create_user('root@example.com', 'pass12345', first_name='Ro', last_name='Ot', is_staff=True)
        self.customer = User.objects.create_user('shopper@example.com', 'pass12345', first_name='Sh', last_name='Op')
        self.department = Department.objects.create(name='Operations')
        self.category = Category.objects.create(name='Furniture')
        self.order = Order.objects.create(user=self.customer, total_price=Decimal('100'), status='pending')

    def staff_with(self, email, *permissions, role='coordinator'):
        user = User.objects.create_user(email, 'pass12345', first_name='St', last_name='Aff')
        Staff.objects.create(user=user, department=self.department, role=role, permissions=list(permissions), hire_date='2026-01-01')
        return user

    def product_payload(self):
        return {'name': 'Bench', 'description': 'd', 'price': '900', 'stock': 3, 'category': self.category.id}

    def test_products_need_edit_products(self):
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.post('/api/products/', self.product_payload(), format='json').status_code, 403)
        self.client.force_authenticate(self.staff_with('editor@example.com', 'edit_products'))
        self.assertEqual(self.client.post('/api/products/', self.product_payload(), format='json').status_code, 201)

    def test_order_changes_need_manage_orders(self):
        self.client.force_authenticate(self.customer)  # not even on their own order
        self.assertEqual(self.client.patch(f'/api/orders/{self.order.id}/', {'status': 'delivered'}, format='json').status_code, 403)
        self.client.force_authenticate(self.staff_with('orders@example.com', 'manage_orders'))
        self.assertEqual(self.client.patch(f'/api/orders/{self.order.id}/', {'status': 'processing'}, format='json').status_code, 200)

    def test_reporting_staff_can_read_all_orders_but_not_change_them(self):
        self.client.force_authenticate(self.staff_with('analyst@example.com', 'view_reports'))
        self.assertEqual(self.client.get('/api/orders/').data['count'], 1)
        self.assertEqual(self.client.patch(f'/api/orders/{self.order.id}/', {'status': 'processing'}, format='json').status_code, 403)

    def test_user_list_needs_manage_users(self):
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get('/api/users/').status_code, 403)
        self.assertEqual(self.client.get('/api/users/profile/').status_code, 200)
        self.client.force_authenticate(self.staff_with('support@example.com', 'manage_users'))
        self.assertEqual(self.client.get('/api/users/').status_code, 200)

    def test_content_staff_edit_cms_and_see_inactive_items(self):
        from cms.models import Partner
        Partner.objects.create(name='Hidden', is_active=False)
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.post('/api/partners/', {'name': 'X'}, format='json').status_code, 403)
        self.assertEqual(self.client.get('/api/partners/').data['count'], 0)
        self.client.force_authenticate(self.staff_with('web@example.com', 'manage_content'))
        self.assertEqual(self.client.get('/api/partners/').data['count'], 1)
        self.assertEqual(self.client.post('/api/partners/', {'name': 'X'}, format='json').status_code, 201)

    def test_full_admin_keeps_everything(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post('/api/products/', self.product_payload(), format='json').status_code, 201)
        self.assertEqual(self.client.get('/api/users/').status_code, 200)
        self.assertEqual(self.client.get('/api/impact/sponsorship/').status_code, 200)

    def test_staff_manager_cannot_escalate(self):
        manager = self.staff_with('hr@example.com', 'manage_staff', 'view_reports', role='manager')
        self.client.force_authenticate(manager)
        base = {'first_name': 'Ne', 'last_name': 'W', 'email': 'new@example.com', 'department': self.department.id,
                'role': 'intern', 'hire_date': '2026-02-01'}
        self.assertEqual(self.client.post('/api/staff/staff/', {**base, 'admin_access': True}, format='json').status_code, 403)
        self.assertEqual(self.client.post('/api/staff/staff/', {**base, 'permissions': ['manage_payments']}, format='json').status_code, 403)
        self.assertEqual(self.client.post('/api/staff/staff/', {**base, 'permissions': ['view_reports']}, format='json').status_code, 201)

        admin_staff = Staff.objects.create(user=self.admin, department=self.department, role='manager', hire_date='2026-01-01')
        self.assertEqual(self.client.post(f'/api/staff/staff/{admin_staff.id}/reset_password/').status_code, 403)
        self.assertEqual(self.client.post('/api/staff/staff/', {**base, 'email': 'root@example.com'}, format='json').status_code, 403)

    def test_is_staff_flag_does_not_bypass_staff_permissions(self):
        # Staff created with the old "can sign in to the admin" box ticked have is_staff=True
        user = self.staff_with('ticked@example.com', 'manage_orders')
        user.is_staff = True
        user.save()
        self.client.force_authenticate(user)
        self.assertFalse(self.client.get('/api/staff/me/').data['is_admin'])
        self.assertEqual(self.client.post('/api/products/', self.product_payload(), format='json').status_code, 403)
        self.assertEqual(self.client.get('/api/users/').status_code, 403)
        self.assertEqual(self.client.patch(f'/api/orders/{self.order.id}/', {'status': 'processing'}, format='json').status_code, 200)

    def test_superuser_with_staff_profile_keeps_full_access(self):
        owner = User.objects.create_superuser('owner@example.com', 'pass12345', first_name='Ow', last_name='Ner')
        Staff.objects.create(user=owner, department=self.department, role='manager', permissions=[], hire_date='2026-01-01')
        self.client.force_authenticate(owner)
        self.assertTrue(self.client.get('/api/staff/me/').data['is_admin'])
        self.assertEqual(self.client.get('/api/users/').status_code, 200)
