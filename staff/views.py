from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
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
