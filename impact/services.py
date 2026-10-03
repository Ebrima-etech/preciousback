"""Impact tracking logic: recording sales from orders and building summaries."""
import logging
from datetime import date
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from .constants import COUNTED_ORDER_STATUSES, GRAMS_PER_BOTTLE, PLASTIC_TYPE_CHOICES
from .models import ImpactEntry

logger = logging.getLogger(__name__)

ZERO = Decimal('0')
COLLECTION_SOURCES = ('collection', 'event')


def _num(value, places=3):
    return round(float(value or 0), places)


# --- Sales --------------------------------------------------------------------

def _sale_values(item):
    product = item.product
    qty = Decimal(item.quantity)
    order_number = item.order.order_number or item.order_id
    return {
        'source': ImpactEntry.SOURCE_SALE,
        'title': f'Order {order_number}: {product.name} x{item.quantity}',
        'product': product,
        'plastic_type': product.plastic_type,
        'plastic_kg': product.plastic_recycled_kg * qty,
        'co2_saved_kg': product.co2_saved_kg * qty,
        'water_saved_liters': product.water_saved_liters * qty,
        'items_count': item.quantity,
    }


def sync_order_impact(order):
    """Record sale entries for a confirmed order, or remove them if it is no longer confirmed.

    Values are a snapshot of the product's impact at the time the order was confirmed.
    """
    try:
        if order.status in COUNTED_ORDER_STATUSES:
            existing = set(
                ImpactEntry.objects.filter(order_item__order=order).values_list('order_item_id', flat=True)
            )
            for item in order.items.select_related('product', 'order'):
                if item.id not in existing:
                    ImpactEntry.objects.create(order_item=item, date=timezone.localdate(), **_sale_values(item))
        else:
            ImpactEntry.objects.filter(order_item__order=order).delete()
    except Exception:
        # Impact tracking must never block order processing
        logger.exception('Failed to sync impact for order %s', order.pk)


def rebuild_sales_impact(refresh=False):
    """Make sale entries match confirmed orders.

    Creates missing entries, removes entries for orders that are no longer confirmed and,
    with refresh=True, recalculates existing entries from current product impact values.
    """
    from orders.models import OrderItem

    removed, _ = ImpactEntry.objects.filter(order_item__isnull=False).exclude(
        order_item__order__status__in=COUNTED_ORDER_STATUSES
    ).delete()

    entries = {
        e.order_item_id: e
        for e in ImpactEntry.objects.filter(order_item__isnull=False)
    }
    created = updated = 0
    items = OrderItem.objects.filter(order__status__in=COUNTED_ORDER_STATUSES).select_related('product', 'order')
    for item in items:
        values = _sale_values(item)
        entry = entries.get(item.id)
        if entry is None:
            ImpactEntry.objects.create(
                order_item=item, date=timezone.localdate(item.order.created_at), **values
            )
            created += 1
        elif refresh:
            for field, value in values.items():
                setattr(entry, field, value)
            entry.save()
            updated += 1

    return {'created': created, 'updated': updated, 'removed': removed}


# --- Summaries ----------------------------------------------------------------

def filter_entries(start=None, end=None):
    qs = ImpactEntry.objects.all()
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lte=end)
    return qs


def compute_totals(qs=None):
    qs = ImpactEntry.objects.all() if qs is None else qs
    agg = qs.aggregate(
        plastic_collected=Sum('plastic_kg', filter=Q(source__in=COLLECTION_SOURCES), default=ZERO),
        plastic_adjusted=Sum('plastic_kg', filter=Q(source='adjustment'), default=ZERO),
        plastic_sold=Sum('plastic_kg', filter=Q(source='sale'), default=ZERO),
        co2=Sum('co2_saved_kg', default=ZERO),
        water=Sum('water_saved_liters', default=ZERO),
        products_sold=Sum('items_count', filter=Q(source='sale'), default=0),
        items_produced=Sum('items_count', filter=Q(source='production'), default=0),
        people=Sum('people_engaged', default=0),
        entries=Count('id'),
    )
    collected = agg['plastic_collected'] + agg['plastic_adjusted']
    # Plastic in sold products was collected at some point, so adding both would double count.
    # Use whichever is larger: logged collections, or plastic shipped in products.
    diverted = max(collected, agg['plastic_sold'])
    return {
        'plastic_diverted_kg': _num(diverted),
        'plastic_collected_kg': _num(collected),
        'plastic_in_products_sold_kg': _num(agg['plastic_sold']),
        'co2_saved_kg': _num(agg['co2']),
        'water_saved_liters': _num(agg['water'], 2),
        'products_sold': agg['products_sold'],
        'items_produced': agg['items_produced'],
        'people_engaged': agg['people'],
        'bottles_equivalent': int((diverted * 1000) / GRAMS_PER_BOTTLE),
        'entries_count': agg['entries'],
    }


def _month_range(start, end):
    months = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        months.append(date(y, m, 1))
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return months


def compute_monthly(qs, start=None, end=None):
    today = timezone.localdate()
    end = end or today
    if not start:
        # Default: the last 12 months including the current one
        y, m = end.year, end.month - 11
        while m < 1:
            y, m = y - 1, m + 12
        start = date(y, m, 1)
    qs = qs.filter(date__gte=start, date__lte=end)

    rows = (
        qs.annotate(month=TruncMonth('date'))
        .values('month', 'source')
        .annotate(plastic=Sum('plastic_kg'), co2=Sum('co2_saved_kg'), items=Sum('items_count'))
    )
    buckets = {
        mo: {'plastic_collected_kg': ZERO, 'plastic_sold_kg': ZERO, 'co2_saved_kg': ZERO, 'products_sold': 0}
        for mo in _month_range(start, end)
    }
    for row in rows:
        month = row['month']
        if hasattr(month, 'date'):
            month = month.date()
        bucket = buckets.get(month)
        if bucket is None:
            continue
        if row['source'] == 'sale':
            bucket['plastic_sold_kg'] += row['plastic'] or ZERO
            bucket['products_sold'] += row['items'] or 0
        elif row['source'] in COLLECTION_SOURCES or row['source'] == 'adjustment':
            bucket['plastic_collected_kg'] += row['plastic'] or ZERO
        bucket['co2_saved_kg'] += row['co2'] or ZERO

    return [
        {
            'month': mo.strftime('%Y-%m'),
            'plastic_collected_kg': _num(b['plastic_collected_kg']),
            'plastic_sold_kg': _num(b['plastic_sold_kg']),
            'co2_saved_kg': _num(b['co2_saved_kg']),
            'products_sold': b['products_sold'],
        }
        for mo, b in buckets.items()
    ]


def compute_summary(start=None, end=None, include_private=False):
    from products.models import Product

    qs = filter_entries(start, end)
    source_labels = dict(ImpactEntry.SOURCE_CHOICES)
    type_labels = dict(PLASTIC_TYPE_CHOICES)

    by_source = [
        {
            'source': row['source'],
            'label': source_labels.get(row['source'], row['source']),
            'plastic_kg': _num(row['plastic']),
            'co2_saved_kg': _num(row['co2']),
            'items_count': row['items'] or 0,
            'people_engaged': row['people'] or 0,
            'entries': row['entries'],
        }
        for row in qs.values('source').annotate(
            plastic=Sum('plastic_kg'), co2=Sum('co2_saved_kg'), items=Sum('items_count'),
            people=Sum('people_engaged'), entries=Count('id'),
        ).order_by('-plastic')
    ]

    by_plastic_type = [
        {
            'plastic_type': row['plastic_type'] or '',
            'label': type_labels.get(row['plastic_type'], 'Unspecified'),
            'plastic_kg': _num(row['plastic']),
        }
        for row in qs.values('plastic_type').annotate(plastic=Sum('plastic_kg')).order_by('-plastic')
        if row['plastic']
    ]

    by_zone = [
        {'zone_id': row['zone_id'], 'name': row['zone__name'], 'plastic_kg': _num(row['plastic'])}
        for row in qs.filter(zone__isnull=False).values('zone_id', 'zone__name')
        .annotate(plastic=Sum('plastic_kg')).order_by('-plastic')
    ]

    summary = {
        'period': {'start': start.isoformat() if start else None, 'end': end.isoformat() if end else None},
        'totals': compute_totals(qs),
        'by_source': by_source,
        'by_plastic_type': by_plastic_type,
        'by_zone': by_zone,
        'monthly': compute_monthly(qs, start, end),
    }

    if include_private:
        summary['top_products'] = [
            {
                'product_id': row['product_id'],
                'name': row['product__name'],
                'units_sold': row['units'] or 0,
                'plastic_kg': _num(row['plastic']),
                'co2_saved_kg': _num(row['co2']),
            }
            for row in qs.filter(source='sale', product__isnull=False)
            .values('product_id', 'product__name')
            .annotate(units=Sum('items_count'), plastic=Sum('plastic_kg'), co2=Sum('co2_saved_kg'))
            .order_by('-plastic')[:5]
        ]
        active = Product.objects.filter(is_active=True)
        summary['catalog'] = {
            'products_total': active.count(),
            'products_with_impact': active.filter(
                Q(plastic_recycled_kg__gt=0) | Q(co2_saved_kg__gt=0) | Q(water_saved_liters__gt=0)
            ).count(),
        }

    return summary


def product_lifetime_impact(product):
    """Totals from confirmed sales of one product."""
    agg = ImpactEntry.objects.filter(source='sale', product=product).aggregate(
        units=Sum('items_count', default=0),
        plastic=Sum('plastic_kg', default=ZERO),
        co2=Sum('co2_saved_kg', default=ZERO),
        water=Sum('water_saved_liters', default=ZERO),
    )
    return {
        'units_sold': agg['units'],
        'plastic_kg': _num(agg['plastic']),
        'co2_saved_kg': _num(agg['co2']),
        'water_saved_liters': _num(agg['water'], 2),
    }
