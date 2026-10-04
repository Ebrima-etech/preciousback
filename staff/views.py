from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.utils.crypto import get_random_string
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from impact.permissions import IsStaff
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
    permission_classes = [IsStaff]

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
    permission_classes = [IsStaff]

    def create(self, request, *args, **kwargs):
        if request.data.get('user_id'):
            return self._create_for_existing_user(request)

        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''

        if not email:
            return Response({'email': ['Email is required.']}, status=status.HTTP_400_BAD_REQUEST)
        existing_user = User.objects.filter(email__iexact=email).first()
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
