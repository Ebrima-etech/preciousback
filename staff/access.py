"""Who can see and do what in the staff dashboards.

- Full admins (superusers, or users with is_staff) see everything.
- Other users with an active Staff profile get a dashboard built from the
  permissions on their profile.
"""
from rest_framework.permissions import BasePermission

ALL_PERMISSIONS = [
    'view_reports', 'edit_products', 'manage_orders', 'manage_payments', 'manage_users',
    'manage_staff', 'view_analytics', 'manage_inventory', 'export_data', 'create_reports',
]

# Suggested permissions per role, used to prefill the staff form
ROLE_DEFAULT_PERMISSIONS = {
    'manager': ALL_PERMISSIONS,
    'supervisor': ['view_reports', 'manage_orders', 'manage_inventory', 'view_analytics'],
    'accountant': ['view_reports', 'manage_payments', 'view_analytics', 'export_data', 'create_reports'],
    'marketer': ['view_reports', 'view_analytics', 'edit_products'],
    'coordinator': ['manage_orders', 'view_reports', 'view_analytics'],
    'technician': ['manage_inventory', 'edit_products'],
    'deliverer': ['manage_orders'],
    'driver': ['manage_orders'],
    'intern': ['view_reports'],
    'other': [],
}

# Dashboard sections and the permissions that unlock each one (any of them)
MODULES = {
    'orders': {'title': 'Orders', 'permissions': ['manage_orders']},
    'deliveries': {'title': 'Deliveries', 'permissions': ['manage_orders']},
    'sales': {'title': 'Sales', 'permissions': ['view_reports', 'view_analytics', 'manage_payments']},
    'payments': {'title': 'Payments', 'permissions': ['manage_payments']},
    'inventory': {'title': 'Inventory', 'permissions': ['manage_inventory', 'edit_products']},
    'customers': {'title': 'Customers', 'permissions': ['manage_users']},
    'impact': {'title': 'Impact', 'permissions': ['view_analytics', 'create_reports']},
    'team': {'title': 'Team', 'permissions': ['manage_staff']},
}

DELIVERY_ROLES = ('deliverer', 'driver')
# Roles that see their department's budget
BUDGET_ROLES = ('manager', 'supervisor', 'accountant')


def staff_profile(user):
    if not user or not user.is_authenticated:
        return None
    profile = getattr(user, 'staff_profile', None)
    if profile is None or not profile.is_active:
        return None
    return profile


def is_full_admin(user):
    return bool(user and user.is_authenticated and (user.is_superuser or user.is_staff))


def effective_permissions(user):
    if is_full_admin(user):
        return list(ALL_PERMISSIONS)
    profile = staff_profile(user)
    return list(profile.permissions or []) if profile else []


def has_staff_permission(user, code):
    return code in effective_permissions(user)


def modules_for(permissions, role=None):
    """Dashboard sections for a set of permissions. Delivery roles get deliveries instead of the full orders view."""
    perms = set(permissions)
    modules = [key for key, cfg in MODULES.items() if perms.intersection(cfg['permissions'])]
    if 'orders' in modules or 'deliveries' in modules:
        if role in DELIVERY_ROLES:
            modules = [m for m in modules if m != 'orders']
        else:
            modules = [m for m in modules if m != 'deliveries']
    return modules


class IsStaffMember(BasePermission):
    """Full admins, or anyone with an active staff profile."""

    def has_permission(self, request, view):
        return is_full_admin(request.user) or staff_profile(request.user) is not None


class HasStaffPermission(BasePermission):
    """Requires the permission code named by view.required_permission."""

    def has_permission(self, request, view):
        code = getattr(view, 'required_permission', None)
        return bool(code) and has_staff_permission(request.user, code)
