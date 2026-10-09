from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.utils.crypto import get_random_string
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from orders.models import Order
from products.models import Product
from .access import (
    DELIVERY_ROLES, ROLE_DEFAULT_PERMISSIONS, HasStaffPermission, IsStaffMember,
    effective_permissions, has_any_permission, is_full_admin, modules_for, require, staff_profile,
)
from .dashboard import build_dashboard, dashboard_for_department, dashboard_for_staff
from .models import Department, Staff
from .serializers import DepartmentSerializer, StaffSerializer

User = get_user_model()


def _email_quietly(subject, message, recipient):
    try:
        send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', None), [recipient], fail_silently=True)
    except Exception:
        pass


class DepartmentViewSet(viewsets.ModelViewSet):
    """Staff-only: departments include budgets."""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [require('manage_staff')]

    def perform_create(self, serializer):
        if not serializer.validated_data.get('manager'):
            serializer.save(manager=self.request.user)
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'error': 'This department still has staff members. Move or remove them first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class StaffViewSet(viewsets.ModelViewSet):
    """Staff-only: staff records include salaries, addresses and phone numbers."""
    queryset = Staff.objects.select_related('user', 'department').all()
    serializer_class = StaffSerializer
    permission_classes = [require('manage_staff')]

    def _escalation_error(self, target=None):
        """Staff managers who aren't full admins can't create admins or hand out permissions they don't have."""
        user = self.request.user
        if is_full_admin(user):
            return None
        if target is not None and (target.user.is_staff or target.user.is_superuser):
            return Response({'error': 'Only full admins can change an admin’s staff record.'}, status=status.HTTP_403_FORBIDDEN)
        if str(self.request.data.get('admin_access', '')).lower() in ('true', '1', 'yes'):
            return Response({'admin_access': ['Only full admins can grant admin access.']}, status=status.HTTP_403_FORBIDDEN)
        requested = self.request.data.get('permissions')
        if isinstance(requested, list):
            beyond = sorted(set(requested) - set(effective_permissions(user)))
            if beyond:
                return Response(
                    {'permissions': [f'You can only grant permissions you have yourself (not: {", ".join(beyond)}).']},
                    status=status.HTTP_403_FORBIDDEN,
                )
        return None

    def update(self, request, *args, **kwargs):
        error = self._escalation_error(self.get_object())
        if error:
            return error
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        error = self._escalation_error(self.get_object())
        if error:
            return error
        return super().destroy(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        error = self._escalation_error()
        if error:
            return error
        if request.data.get('user_id'):
            return self._create_for_existing_user(request)

        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''

        if not email:
            return Response({'email': ['Email is required.']}, status=status.HTTP_400_BAD_REQUEST)
        existing_user = User.objects.filter(email__iexact=email).first()
        if existing_user and (existing_user.is_staff or existing_user.is_superuser) and not is_full_admin(request.user):
            # Reusing an account resets its password, so only full admins may do it for admin accounts
            return Response({'email': ['Only full admins can add an admin account as staff.']}, status=status.HTTP_403_FORBIDDEN)
        if existing_user and Staff.objects.filter(user=existing_user).exists():
            return Response({'email': ['This person is already a staff member.']}, status=status.HTTP_400_BAD_REQUEST)
        if not (request.data.get('first_name') or '').strip():
            return Response({'first_name': ['First name is required.']}, status=status.HTTP_400_BAD_REQUEST)

        # Validate the staff fields before creating any account, so a bad form never leaves an orphan user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        first_name = validated.pop('first_name', '')
        last_name = validated.pop('last_name', '')
        admin_access = validated.pop('admin_access', False)

        generated = not password or len(password) < 8
        if generated:
            password = get_random_string(12)

        with transaction.atomic():
            if existing_user:
                # Reuse an account without a staff profile, e.g. one left behind by an earlier failed attempt.
                # It gets a fresh password so the admin can hand it over.
                user = existing_user
                user.first_name = first_name
                user.last_name = last_name
                user.is_active = True
                user.is_staff = user.is_staff or admin_access
                if user.is_superuser or user.pk == request.user.pk:
                    generated = False  # never reset the password of a superuser or the admin doing this
                else:
                    user.set_password(password)
                user.save()
            else:
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=admin_access,
                )
            staff = Staff.objects.create(user=user, **validated)

        password_changed = not existing_user or not (user.is_superuser or user.pk == request.user.pk)
        if password_changed:
            _email_quietly(
                'Your Precious Plastic staff account',
                f'Your account has been created.\n\nEmail: {email}\nTemporary password: {password}\n\nPlease log in and change your password.',
                email,
            )

        data = self.get_serializer(staff).data
        data['temporary_password'] = password if generated else None
        data['reused_existing_account'] = bool(existing_user)
        return Response(data, status=status.HTTP_201_CREATED)

    def _create_for_existing_user(self, request):
        """Make an existing user (e.g. a customer account) a staff member. Their password is left alone."""
        try:
            user = User.objects.get(pk=int(request.data.get('user_id')))
        except (User.DoesNotExist, TypeError, ValueError):
            return Response({'user_id': ['User not found.']}, status=status.HTTP_400_BAD_REQUEST)
        if Staff.objects.filter(user=user).exists():
            return Response({'user_id': ['This person is already a staff member.']}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        validated.pop('first_name', None)
        validated.pop('last_name', None)
        admin_access = validated.pop('admin_access', False)

        with transaction.atomic():
            fields = []
            if admin_access and not user.is_staff:
                user.is_staff = True
                fields.append('is_staff')
            if not user.is_active:
                user.is_active = True
                fields.append('is_active')
            if fields:
                user.save(update_fields=fields)
            staff = Staff.objects.create(user=user, **validated)

        data = self.get_serializer(staff).data
        data['temporary_password'] = None
        data['reused_existing_account'] = True
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def candidates(self, request):
        """Users who aren't staff yet, for the "make an existing user staff" search."""
        search = (request.query_params.get('search') or '').strip()
        qs = User.objects.filter(staff_profile__isnull=True, is_active=True).order_by('first_name', 'last_name', 'email')
        if search:
            qs = qs.filter(
                Q(email__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
            )
        return Response([
            {
                'id': u.id,
                'email': u.email,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'phone': getattr(u, 'phone', ''),
                'date_joined': u.date_joined,
            }
            for u in qs[:20]
        ])

    def perform_destroy(self, instance):
        # Remove the staff record and switch off the account; the user is kept because orders may reference it
        user = instance.user
        with transaction.atomic():
            instance.delete()
            if not user.is_superuser:
                user.is_staff = False
                user.is_active = False
                user.save(update_fields=['is_staff', 'is_active'])

    def _set_active(self, staff, active):
        error = self._escalation_error(staff)
        if error:
            return error
        if staff.user_id == self.request.user.id and not active:
            return Response({'error': 'You cannot deactivate your own account.'}, status=status.HTTP_400_BAD_REQUEST)
        staff.is_active = active
        staff.user.is_active = active
        staff.save(update_fields=['is_active', 'updated_at'])
        staff.user.save(update_fields=['is_active'])
        return Response(self.get_serializer(staff).data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        return self._set_active(self.get_object(), False)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        return self._set_active(self.get_object(), True)

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        staff = self.get_object()
        error = self._escalation_error(staff)
        if error:
            return error
        new_password = get_random_string(12)
        staff.user.set_password(new_password)
        staff.user.save()
        _email_quietly(
            'Your password was reset',
            f'Your password has been reset.\n\nNew temporary password: {new_password}\n\nPlease log in and change your password.',
            staff.user.email,
        )
        return Response({'status': 'password reset', 'temporary_password': new_password, 'email': staff.user.email})

    @action(detail=True, methods=['post'])
    def assign_permissions(self, request, pk=None):
        staff = self.get_object()
        error = self._escalation_error(staff)
        if error:
            return error
        serializer = self.get_serializer(staff, data={'permissions': request.data.get('permissions', [])}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_department(self, request):
        department_id = request.query_params.get('department_id')
        if not department_id:
            return Response({'error': 'department_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        staff = self.get_queryset().filter(department_id=department_id, is_active=True)
        return Response(self.get_serializer(staff, many=True).data)

    @action(detail=False, methods=['get'])
    def by_role(self, request):
        role = request.query_params.get('role')
        if not role:
            return Response({'error': 'role parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        staff = self.get_queryset().filter(role=role, is_active=True)
        return Response(self.get_serializer(staff, many=True).data)


# --- Staff dashboards -------------------------------------------------------------



class StaffMeView(APIView):
    """Who the signed-in staff member is and which dashboard sections they get."""
    permission_classes = [IsStaffMember]

    def get(self, request):
        user = request.user
        profile = staff_profile(user)
        permissions = effective_permissions(user)
        return Response({
            'is_admin': is_full_admin(user),
            'user': {'id': user.id, 'name': user.get_full_name() or user.email, 'email': user.email},
            'staff': {
                'id': profile.id,
                'role': profile.role,
                'role_display': profile.get_role_display(),
                'department_id': profile.department_id,
                'department': profile.department.name,
            } if profile else None,
            'permissions': permissions,
            'modules': modules_for(permissions, profile.role if profile else None),
        })


class StaffDashboardView(APIView):
    """A staff member's own dashboard. Admins can view any department (?department=) or staff member (?staff=)."""
    permission_classes = [IsStaffMember]

    def get(self, request):
        user = request.user
        admin = is_full_admin(user)
        department_id = request.query_params.get('department')
        staff_id = request.query_params.get('staff')

        if (department_id or staff_id) and not (admin or has_any_permission(user, 'manage_staff')):
            return Response({'error': 'Only admins and staff managers can view other dashboards.'}, status=status.HTTP_403_FORBIDDEN)
        if department_id:
            department = Department.objects.filter(pk=department_id).first()
            if not department:
                return Response({'error': 'Department not found.'}, status=status.HTTP_404_NOT_FOUND)
            return Response({'viewing': {'type': 'department', 'name': department.name}, **dashboard_for_department(department)})
        if staff_id:
            staff = Staff.objects.select_related('user', 'department').filter(pk=staff_id).first()
            if not staff:
                return Response({'error': 'Staff member not found.'}, status=status.HTTP_404_NOT_FOUND)
            name = staff.user.get_full_name() or staff.user.email
            return Response({
                'viewing': {'type': 'staff', 'name': name, 'role': staff.get_role_display()},
                **dashboard_for_staff(staff, viewer_is_admin=True),
            })

        profile = staff_profile(user)
        if profile and not admin:
            return Response({'viewing': {'type': 'self'}, **dashboard_for_staff(profile)})
        # Admins without (or with) a profile: every section, plus their department if they have one
        data = build_dashboard(
            permissions=effective_permissions(user),
            department=profile.department if profile else None,
            show_budget=True, show_contacts=True,
        )
        return Response({'viewing': {'type': 'self'}, **data})


class StaffOrderStatusView(APIView):
    """Change an order's status from the dashboard. Drivers/deliverers can only move orders out for delivery."""
    permission_classes = [HasStaffPermission]
    required_permission = 'manage_orders'

    def post(self, request, pk):
        order = Order.objects.filter(pk=pk).first()
        if not order:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        new_status = request.data.get('status')
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({'error': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)

        profile = staff_profile(request.user)
        if profile and profile.role in DELIVERY_ROLES and not is_full_admin(request.user):
            allowed = {('processing', 'shipped'), ('shipped', 'delivered'), ('processing', 'delivered')}
            if (order.status, new_status) not in allowed:
                return Response(
                    {'error': 'Deliveries can only be marked as shipped or delivered.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        order.status = new_status
        order.save()  # triggers impact tracking
        return Response({'id': order.id, 'status': order.status, 'status_label': order.get_status_display()})


class StaffStockView(APIView):
    """Set a product's stock level from the inventory dashboard."""
    permission_classes = [HasStaffPermission]
    required_permission = 'manage_inventory'

    def post(self, request, pk):
        product = Product.objects.filter(pk=pk).first()
        if not product:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            stock = int(request.data.get('stock'))
        except (TypeError, ValueError):
            return Response({'error': 'Stock must be a whole number.'}, status=status.HTTP_400_BAD_REQUEST)
        if stock < 0 or stock > 1_000_000:
            return Response({'error': 'Stock must be between 0 and 1,000,000.'}, status=status.HTTP_400_BAD_REQUEST)
        product.stock = stock
        product.save(update_fields=['stock', 'updated_at'])
        return Response({'id': product.id, 'name': product.name, 'stock': product.stock})


class RoleDefaultsView(APIView):
    """Suggested permissions per role, used to prefill the staff form."""
    permission_classes = [require('manage_staff')]

    def get(self, request):
        return Response(ROLE_DEFAULT_PERMISSIONS)


class StaffBudgetView(APIView):
    """Each department's yearly budget compared with what its active staff cost in salaries."""
    permission_classes = [require('manage_staff', 'manage_payments')]

    def get(self, request):
        from decimal import Decimal
        from django.db.models import Count, Sum

        zero = Decimal('0')
        departments = Department.objects.annotate(
            monthly_salaries=Sum('staff_members__salary', filter=Q(staff_members__is_active=True), default=zero),
            active_staff=Count('staff_members', filter=Q(staff_members__is_active=True)),
            unsalaried=Count('staff_members', filter=Q(staff_members__is_active=True, staff_members__salary__isnull=True)),
        ).order_by('name')

        rows = []
        totals = {'budget': zero, 'monthly_salaries': zero, 'yearly_salaries': zero}
        for dept in departments:
            monthly = dept.monthly_salaries or zero
            yearly = monthly * 12
            budget = dept.budget_allocation or zero
            rows.append({
                'id': dept.id,
                'name': dept.name,
                'is_active': dept.is_active,
                'budget': float(budget),
                'active_staff': dept.active_staff,
                'staff_without_salary': dept.unsalaried,
                'monthly_salaries': float(monthly),
                'yearly_salaries': float(yearly),
                'remaining': float(budget - yearly),
                'used_percent': round(float(yearly / budget * 100), 1) if budget > 0 else None,
            })
            totals['budget'] += budget
            totals['monthly_salaries'] += monthly
            totals['yearly_salaries'] += yearly

        return Response({
            'currency': 'GMD',
            'assumptions': 'Budgets are per year; staff salaries are per month (x12 for the yearly cost).',
            'departments': rows,
            'totals': {
                'budget': float(totals['budget']),
                'monthly_salaries': float(totals['monthly_salaries']),
                'yearly_salaries': float(totals['yearly_salaries']),
                'remaining': float(totals['budget'] - totals['yearly_salaries']),
                'used_percent': round(float(totals['yearly_salaries'] / totals['budget'] * 100), 1) if totals['budget'] > 0 else None,
            },
        })
