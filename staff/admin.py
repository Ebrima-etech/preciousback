from django.contrib import admin
from .models import Department, Staff

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'budget_allocation', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'role', 'department', 'hire_date', 'is_active']
    list_filter = ['role', 'department', 'is_active', 'hire_date']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Position', {
            'fields': ('department', 'role', 'permissions')
        }),
        ('Compensation', {
            'fields': ('salary', 'hire_date')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'address', 'emergency_contact', 'emergency_contact_phone')
        }),
        ('Status', {
            'fields': ('is_active', 'notes')
        }),
    )

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Staff Name'
