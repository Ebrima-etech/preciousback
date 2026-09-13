from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Department, Staff

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class DepartmentSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    staff_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'manager', 'manager_name', 'budget_allocation', 'is_active', 'staff_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_staff_count(self, obj):
        return obj.staff_members.count()

class StaffSerializer(serializers.ModelSerializer):
    user_data = UserSerializer(source='user', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Staff
        fields = ['id', 'user', 'user_data', 'department', 'department_name', 'role', 'role_display', 'permissions', 'salary', 'hire_date', 'is_active', 'phone_number', 'address', 'emergency_contact', 'emergency_contact_phone', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
