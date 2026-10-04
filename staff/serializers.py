from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Department, Staff

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login']

class DepartmentSerializer(serializers.ModelSerializer):
    manager_name = serializers.SerializerMethodField()
    staff_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'manager', 'manager_name', 'budget_allocation', 'is_active', 'staff_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_manager_name(self, obj):
        return obj.manager.get_full_name() if obj.manager else None

    def get_staff_count(self, obj):
        return obj.staff_members.count()

class StaffSerializer(serializers.ModelSerializer):
    user_data = UserSerializer(source='user', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    # Account fields live on the User; accepted here so one form can edit everything
    first_name = serializers.CharField(write_only=True, required=False, max_length=150)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=150)
    admin_access = serializers.BooleanField(
        required=False, help_text='Lets this person sign in to the admin dashboard (sets user.is_staff)'
    )

    class Meta:
        model = Staff
        fields = ['id', 'user', 'user_data', 'department', 'department_name', 'role', 'role_display', 'permissions',
                  'salary', 'hire_date', 'is_active', 'phone_number', 'address', 'emergency_contact',
                  'emergency_contact_phone', 'notes', 'first_name', 'last_name', 'admin_access',
                  'created_at', 'updated_at']
        read_only_fields = ['user', 'is_active', 'created_at', 'updated_at']

    def validate_permissions(self, value):
        valid = {code for code, _ in Staff.PERMISSION_CHOICES}
        if not isinstance(value, list) or any(p not in valid for p in value):
            raise serializers.ValidationError('Unknown permission code.')
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['admin_access'] = instance.user.is_staff
        return data

    def update(self, instance, validated_data):
        user = instance.user
        user_changed = False
        for field in ('first_name', 'last_name'):
            if field in validated_data:
                setattr(user, field, validated_data.pop(field))
                user_changed = True
        if 'admin_access' in validated_data:
            user.is_staff = validated_data.pop('admin_access')
            user_changed = True
        if user_changed:
            user.save()
        return super().update(instance, validated_data)
