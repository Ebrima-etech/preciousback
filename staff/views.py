from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from .models import Department, Staff
from .serializers import DepartmentSerializer, StaffSerializer, UserSerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Department.objects.all()
        return Department.objects.filter(manager=self.request.user)

class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.select_related('user', 'department')
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Staff.objects.select_related('user', 'department')
        return Staff.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        email = data.get('email', '')
        
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({'error': 'User with this email already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        password = get_random_string(12)
        username = email.split('@')[0] + '_' + get_random_string(4)
        
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        
        data['user'] = user.id
        
        try:
            send_mail(
                'Your Staff Account Created',
                f'Your account has been created.\n\nEmail: {email}\nTemporary Password: {password}\n\nPlease log in and change your password.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
        except Exception as e:
            pass
        
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        staff = self.get_object()
        staff.is_active = False
        staff.user.is_active = False
        staff.save()
        staff.user.save()
        return Response({'status': 'staff deactivated'})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        staff = self.get_object()
        staff.is_active = True
        staff.user.is_active = True
        staff.save()
        staff.user.save()
        return Response({'status': 'staff activated'})

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        staff = self.get_object()
        new_password = get_random_string(12)
        staff.user.set_password(new_password)
        staff.user.save()
        
        try:
            send_mail(
                'Password Reset',
                f'Your password has been reset.\n\nNew Temporary Password: {new_password}\n\nPlease log in and change your password.',
                settings.DEFAULT_FROM_EMAIL,
                [staff.user.email],
                fail_silently=True,
            )
        except Exception as e:
            pass
        
        return Response({
            'status': 'password reset',
            'temporary_password': new_password,
            'email': staff.user.email
        })

    @action(detail=True, methods=['post'])
    def assign_permissions(self, request, pk=None):
        staff = self.get_object()
        permissions = request.data.get('permissions', [])
        staff.permissions = permissions
        staff.save()
        return Response({'status': 'permissions assigned'})

    @action(detail=False, methods=['get'])
    def by_department(self, request):
        department_id = request.query_params.get('department_id')
        if department_id:
            staff = Staff.objects.filter(department_id=department_id, is_active=True)
            serializer = self.get_serializer(staff, many=True)
            return Response(serializer.data)
        return Response({'error': 'department_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_role(self, request):
        role = request.query_params.get('role')
        if role:
            staff = Staff.objects.filter(role=role, is_active=True)
            serializer = self.get_serializer(staff, many=True)
            return Response(serializer.data)
        return Response({'error': 'role parameter required'}, status=status.HTTP_400_BAD_REQUEST)
