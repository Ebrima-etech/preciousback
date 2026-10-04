"""Data for the role- and department-based staff dashboards."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from impact.constants import COUNTED_ORDER_STATUSES
from orders.models import Order, OrderItem
from products.models import Product
from .access import BUDGET_ROLES, modules_for
from .models import Department, Staff

ZERO = Decimal('0')
LOW_STOCK = 5


def _money(value):
    return round(float(value or 0), 2)


def _delivery_details(order):
    """Delivery info from the order's address fields, falling back to the notes older orders used."""
    details = {}
    for line in (order.notes or '').splitlines():
        key, sep, value = line.partition(':')
        if sep:
            details[key.strip().lower().replace(' ', '_')] = value.strip()
    lines = order.shipping_address_lines()
    if order.is_international:
        location = ', '.join(lines[1:])  # everything after the name
    else:
        location = order.delivery_location or details.get('location', '')
    return {
        'deliver_to': order.shipping_name or details.get('deliver_to', ''),
        'phone': order.shipping_phone or details.get('phone', ''),
        'location': location,
        'international': order.is_international,
        'country': order.shipping_country,
        'address_lines': lines,
    }


def _order_row(order):
    items = list(order.items.all())
    customer = order.user.get_full_name() or order.user.email
    return {
        'id': order.id,
        'order_number': order.order_number,
        'status': order.status,
        'status_label': order.get_status_display(),
        'payment_method': order.payment_method,
        'total': _money(order.total_price),
        'created_at': order.created_at,
        'customer': customer,
        'items': [f'{item.product.name} x{item.quantity}' for item in items],
        'delivery': _delivery_details(order),
    }


# --- Sections -------------------------------------------------------------------

def orders_section():
    today = timezone.localdate()
    counts = dict(Order.objects.values_list('status').annotate(n=Count('id')))
    queue = (
        Order.objects.filter(status__in=['pending', 'processing'])
        .select_related('user').prefetch_related('items__product').order_by('created_at')[:15]
    )
    return {
        'counts': {status: counts.get(status, 0) for status, _ in Order.STATUS_CHOICES},
        'today': Order.objects.filter(created_at__date=today).count(),
        'queue': [_order_row(o) for o in queue],
    }


def deliveries_section():
    to_deliver = (
        Order.objects.filter(status__in=['processing', 'shipped'])
        .select_related('user').prefetch_related('items__product').order_by('created_at')[:25]
    )
    today = timezone.localdate()
    return {
        'ready': Order.objects.filter(status='processing').count(),
        'on_the_way': Order.objects.filter(status='shipped').count(),
        'delivered_today': Order.objects.filter(status='delivered', updated_at__date=today).count(),
        'orders': [_order_row(o) for o in to_deliver],
    }


def sales_section():
    now = timezone.now()
    confirmed = Order.objects.filter(status__in=COUNTED_ORDER_STATUSES)

    def window(start, end=None):
        qs = confirmed.filter(created_at__gte=start)
        if end:
            qs = qs.filter(created_at__lt=end)
        agg = qs.aggregate(revenue=Sum('total_price', default=ZERO), orders=Count('id'))
        return {'revenue': _money(agg['revenue']), 'orders': agg['orders']}

    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_30 = window(now - timedelta(days=30))
    prev_30 = window(now - timedelta(days=60), now - timedelta(days=30))

    since = day_start - timedelta(days=13)
    daily = {
        row['day']: row
        for row in confirmed.filter(created_at__gte=since)
        .annotate(day=TruncDate('created_at')).values('day')
        .annotate(revenue=Sum('total_price'), orders=Count('id'))
    }
    series = []
    for i in range(14):
        day = (since + timedelta(days=i)).date()
        row = daily.get(day)
        series.append({'date': day.isoformat(), 'revenue': _money(row['revenue']) if row else 0.0, 'orders': row['orders'] if row else 0})

    line_total = ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField(max_digits=14, decimal_places=2))
    top_products = (
        OrderItem.objects.filter(order__status__in=COUNTED_ORDER_STATUSES, order__created_at__gte=now - timedelta(days=30))
        .values('product_id', 'product__name')
        .annotate(units=Sum('quantity'), revenue=Sum(line_total))
        .order_by('-revenue')[:5]
    )

    return {
        'today': window(day_start),
        'last_7_days': window(now - timedelta(days=7)),
        'last_30_days': last_30,
        'previous_30_days': prev_30,
        'average_order_value': _money(last_30['revenue'] / last_30['orders']) if last_30['orders'] else 0.0,
        'daily': series,
        'top_products': [
            {'product_id': r['product_id'], 'name': r['product__name'], 'units': r['units'], 'revenue': _money(r['revenue'])}
            for r in top_products
        ],
    }


def payments_section():
    since = timezone.now() - timedelta(days=30)
    awaiting = Order.objects.filter(status='payment_pending').aggregate(n=Count('id'), amount=Sum('total_price', default=ZERO))
    cash_due = Order.objects.filter(payment_method='cod', status__in=['pending', 'processing', 'shipped']).aggregate(
        n=Count('id'), amount=Sum('total_price', default=ZERO)
    )
    by_method = (
        Order.objects.filter(status__in=COUNTED_ORDER_STATUSES, created_at__gte=since)
        .values('payment_method').annotate(n=Count('id'), amount=Sum('total_price'))
    )
    labels = dict(Order.PAYMENT_METHOD_CHOICES)
    return {
        'awaiting_online_payment': {'orders': awaiting['n'], 'amount': _money(awaiting['amount'])},
        'cash_on_delivery_due': {'orders': cash_due['n'], 'amount': _money(cash_due['amount'])},
        'by_method_30_days': [
            {'method': r['payment_method'], 'label': labels.get(r['payment_method'], r['payment_method']),
             'orders': r['n'], 'amount': _money(r['amount'])}
            for r in by_method
        ],
    }


def inventory_section():
    active = Product.objects.filter(is_active=True)
    fields = ('id', 'name', 'stock')
    return {
        'active_products': active.count(),
        'out_of_stock_count': active.filter(stock=0).count(),
        'low_stock_count': active.filter(stock__gt=0, stock__lte=LOW_STOCK).count(),
        'low_stock_threshold': LOW_STOCK,
        'out_of_stock': list(active.filter(stock=0).order_by('name').values(*fields)[:15]),
        'low_stock': list(active.filter(stock__gt=0, stock__lte=LOW_STOCK).order_by('stock', 'name').values(*fields)[:15]),
        'missing_impact': active.filter(plastic_recycled_kg=0, co2_saved_kg=0, water_saved_liters=0).count(),
    }


def customers_section():
    User = get_user_model()
    now = timezone.now()
    customers = User.objects.filter(is_staff=False, is_superuser=False, staff_profile__isnull=True)
    recent = customers.order_by('-date_joined')[:8]
    return {
        'total': customers.count(),
        'new_7_days': customers.filter(date_joined__gte=now - timedelta(days=7)).count(),
        'new_30_days': customers.filter(date_joined__gte=now - timedelta(days=30)).count(),
        'with_orders': customers.filter(orders__isnull=False).distinct().count(),
        'recent': [
            {'id': u.id, 'name': u.get_full_name() or u.email, 'email': u.email, 'date_joined': u.date_joined}
            for u in recent
        ],
    }


def impact_section():
    from impact.services import compute_totals, filter_entries

    today = timezone.localdate()
    return {
        'all_time': compute_totals(),
        'this_month': compute_totals(filter_entries(start=today.replace(day=1), end=today)),
    }


def team_section():
    active = Staff.objects.filter(is_active=True)
    by_department = (
        active.values('department_id', 'department__name').annotate(n=Count('id')).order_by('department__name')
    )
    roles = dict(Staff.ROLE_CHOICES)
    by_role = active.values('role').annotate(n=Count('id')).order_by('-n')
    recent = Staff.objects.select_related('user', 'department').order_by('-hire_date')[:5]
    return {
        'active': active.count(),
        'inactive': Staff.objects.filter(is_active=False).count(),
        'by_department': [{'department_id': r['department_id'], 'name': r['department__name'], 'count': r['n']} for r in by_department],
        'by_role': [{'role': r['role'], 'label': roles.get(r['role'], r['role']), 'count': r['n']} for r in by_role],
        'recent_hires': [
            {'name': s.user.get_full_name() or s.user.email, 'role': s.get_role_display(),
             'department': s.department.name, 'hire_date': s.hire_date}
            for s in recent
        ],
    }


SECTION_BUILDERS = {
    'orders': orders_section,
    'deliveries': deliveries_section,
    'sales': sales_section,
    'payments': payments_section,
    'inventory': inventory_section,
    'customers': customers_section,
    'impact': impact_section,
    'team': team_section,
}


def department_section(department, show_budget=False, show_contacts=False):
    members = department.staff_members.filter(is_active=True).select_related('user').order_by('role', 'user__first_name')
    data = {
        'id': department.id,
        'name': department.name,
        'description': department.description,
        'manager': department.manager.get_full_name() if department.manager else None,
        'member_count': members.count(),
        'members': [
            {
                'id': m.id,
                'name': m.user.get_full_name() or m.user.email,
                'role': m.get_role_display(),
                'email': m.user.email,
                **({'phone': m.phone_number} if show_contacts else {}),
            }
            for m in members
        ],
    }
    if show_budget:
        data['budget_allocation'] = _money(department.budget_allocation)
    return data


def build_dashboard(*, permissions, role=None, department=None, show_budget=False, show_contacts=False):
    modules = modules_for(permissions, role)
    return {
        'modules': modules,
        'sections': {key: SECTION_BUILDERS[key]() for key in modules},
        'department': department_section(department, show_budget, show_contacts) if department else None,
    }


def dashboard_for_staff(staff, viewer_is_admin=False):
    return build_dashboard(
        permissions=staff.permissions or [],
        role=staff.role,
        department=staff.department,
        show_budget=viewer_is_admin or staff.role in BUDGET_ROLES or 'manage_staff' in (staff.permissions or []),
        show_contacts=viewer_is_admin or 'manage_staff' in (staff.permissions or []),
    )


def dashboard_for_department(department):
    """Admin view of a department: everything its active members can see, combined."""
    members = list(department.staff_members.filter(is_active=True))
    permissions = sorted({p for m in members for p in (m.permissions or [])})
    roles = {m.role for m in members}
    role = 'driver' if roles and roles <= {'deliverer', 'driver'} else None
    return build_dashboard(permissions=permissions, role=role, department=department, show_budget=True, show_contacts=True)
