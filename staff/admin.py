from django.contrib import admin
from django.utils.html import format_html
from .models import Department, Staff

class StaffInline(admin.TabularInline):
    model = Staff
    extra = 0
    fields = ('user', 'role', 'salary', 'hire_date', 'is_active')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager_name', 'budget_display', 'staff_count_display', 'status_badge', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'manager__first_name', 'manager__last_name']
    readonly_fields = ['created_at', 'updated_at', 'staff_count_display']
    inlines = [StaffInline]
    fieldsets = (
        ('Department Information', {
            'fields': ('name', 'description')
        }),
        ('Management', {
            'fields': ('manager', 'budget_allocation')
        }),
        ('Staffing', {
            'fields': ('staff_count_display',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def manager_name(self, obj):
        return obj.manager.get_full_name() if obj.manager else '-'
    manager_name.short_description = 'Manager'

    def budget_display(self, obj):
        return f'D {obj.budget_allocation:,.2f}'
    budget_display.short_description = 'Budget Allocation'

    def staff_count_display(self, obj):
        count = obj.staff_members.count()
        return format_html(
            '<span style="background-color: #e0f2fe; padding: 3px 8px; border-radius: 4px;"><strong>{}</strong></span>',
            count
        )
    staff_count_display.short_description = 'Total Staff Members'

    def status_badge(self, obj):
        if obj.is_active:
            color = 'green'
            text = 'Active'
        else:
            color = 'red'
            text = 'Inactive'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, text
        )
    status_badge.short_description = 'Status'

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'email_display', 'role_badge', 'department_display', 'hire_date', 'status_badge']
    list_filter = ['role', 'department', 'is_active', 'hire_date']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'phone_number']
    readonly_fields = ['created_at', 'updated_at', 'permissions_display']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'email_display')
        }),
        ('Position Details', {
            'fields': ('department', 'role', 'hire_date')
        }),
        ('Compensation & Benefits', {
            'fields': ('salary',)
        }),
        ('Permissions', {
            'fields': ('permissions', 'permissions_display'),
            'classes': ('collapse',),
            'description': 'Select which permissions this staff member has access to.'
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'address')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact', 'emergency_contact_phone'),
            'classes': ('collapse',)
        }),
        ('Additional Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Staff Name'
    get_full_name.admin_order_field = 'user__first_name'

    def email_display(self, obj):
        return obj.user.email
    email_display.short_description = 'Email'
    email_display.admin_order_field = 'user__email'

    def department_display(self, obj):
        return obj.department.name
    department_display.short_description = 'Department'
    department_display.admin_order_field = 'department__name'

    def role_badge(self, obj):
        colors = {
            'manager': '#8b5cf6',
            'marketer': '#ec4899',
            'deliverer': '#06b6d4',
            'accountant': '#f59e0b',
            'technician': '#10b981',
            'driver': '#3b82f6',
            'coordinator': '#6366f1',
            'supervisor': '#d946ef',
            'intern': '#14b8a6',
            'other': '#6b7280'
        }
        color = colors.get(obj.role, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = 'Role'
    role_badge.admin_order_field = 'role'

    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 10px; border-radius: 3px;">Inactive</span>'
            )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'is_active'

    def permissions_display(self, obj):
        if not obj.permissions:
            return 'No permissions assigned'
        permissions_html = '<ul style="margin: 0; padding-left: 20px;">'
        for perm in obj.permissions:
            permissions_html += f'<li>{perm}</li>'
        permissions_html += '</ul>'
        return format_html(permissions_html)
    permissions_display.short_description = 'Current Permissions'

    actions = ['mark_active', 'mark_inactive']

    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} staff member(s) marked as active.')
    mark_active.short_description = 'Mark selected staff members as active'

    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} staff member(s) marked as inactive.')
    mark_inactive.short_description = 'Mark selected staff members as inactive'
