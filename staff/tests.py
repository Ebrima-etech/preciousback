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
