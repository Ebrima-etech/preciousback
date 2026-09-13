from django.db import models
from django.conf import settings

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')
    budget_allocation = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Departments"

    def __str__(self):
        return self.name


class Staff(models.Model):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('marketer', 'Marketer'),
        ('deliverer', 'Deliverer'),
        ('accountant', 'Accountant'),
        ('technician', 'Technician'),
        ('driver', 'Driver'),
        ('coordinator', 'Coordinator'),
        ('supervisor', 'Supervisor'),
        ('intern', 'Intern'),
        ('other', 'Other'),
    ]

    PERMISSION_CHOICES = [
        ('view_reports', 'View Reports'),
        ('edit_products', 'Edit Products'),
        ('manage_orders', 'Manage Orders'),
        ('manage_payments', 'Manage Payments'),
        ('manage_users', 'Manage Users'),
        ('manage_staff', 'Manage Staff'),
        ('view_analytics', 'View Analytics'),
        ('manage_inventory', 'Manage Inventory'),
        ('export_data', 'Export Data'),
        ('create_reports', 'Create Reports'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_profile')
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='staff_members')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    permissions = models.JSONField(default=list, blank=True, help_text="List of permission codes")
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hire_date = models.DateField()
    is_active = models.BooleanField(default=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Staff"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"

    def has_permission(self, permission_code):
        return permission_code in (self.permissions or [])
