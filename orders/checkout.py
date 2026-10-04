"""Checkout validation for Gambian and international orders."""
from decimal import Decimal, InvalidOperation

from decouple import config
from rest_framework import status
from rest_framework.response import Response

from products.models import Location, Product
from .countries import COUNTRIES, HOME_COUNTRY, country_name

DEFAULT_INTERNATIONAL_SHIPPING_FEE = Decimal('2500')


def international_shipping_fee():
    """Flat shipping fee (GMD) for orders outside The Gambia. Set INTERNATIONAL_SHIPPING_FEE on the server to change it."""
    try:
        return Decimal(str(config('INTERNATIONAL_SHIPPING_FEE', default=str(DEFAULT_INTERNATIONAL_SHIPPING_FEE))))
    except (InvalidOperation, ValueError):
        return DEFAULT_INTERNATIONAL_SHIPPING_FEE


def gambia_delivery_fee(products, location):
    """Same rule the checkout page shows: each product's delivery price for the location, once per product.

    Products without a price for the location deliver for free.
    """
    fee = Decimal('0')
    for product in products:
        price = (product.delivery_prices or {}).get(str(location.id))
        if price in (None, ''):
            continue
        try:
            fee += Decimal(str(price))
        except (InvalidOperation, ValueError):
            continue
    return fee


def _check_expected_total(data, order_fields, order_items, total):
    """Totals are always calculated here. If the customer saw a different total (e.g. a price changed while the
    page was open), stop instead of charging an amount they didn't see."""
    expected = data.get('total_amount')
    if expected not in (None, ''):
        try:
            expected = Decimal(str(expected))
        except (InvalidOperation, ValueError):
            expected = None
        if expected is None or abs(expected - total) > Decimal('0.01'):
            return Response(
                {
                    'error': f'Prices have changed since you opened this page. The correct total is D {total:,.2f}. '
                             'Please refresh the page and try again.',
                    'total': float(total),
                },
                status=status.HTTP_409_CONFLICT,
            )
    return order_fields, order_items, total


def _clean(data, key, max_length=255):
    return str(data.get(key) or '').strip()[:max_length]


def _error(fields):
    return Response(fields, status=status.HTTP_400_BAD_REQUEST)


def _parse_items(raw_items):
    """Returns [(product_id, quantity, client_price)] or an error message."""
    if not isinstance(raw_items, list) or not raw_items:
        return 'Your cart is empty.'
    parsed = []
    for item in raw_items:
        try:
            product_id = int(item['product_id'])
            quantity = int(item['quantity'])
        except (KeyError, TypeError, ValueError):
            return 'Invalid cart item.'
        if quantity < 1 or quantity > 1000:
            return 'Invalid quantity.'
        parsed.append((product_id, quantity, item.get('price')))
    return parsed


def prepare_checkout(data):
    """Validate checkout data.

    Returns (order_fields, order_items, total) or an error Response.
    - The Gambia: delivery location; delivery fee from each product's price for that location.
    - Elsewhere: full postal address plus the flat international shipping fee.
    Product prices always come from the database; client-sent prices are ignored.
    """
    for field in ('items', 'return_url', 'cancel_url'):
        if field not in data:
            return _error({'error': f'Missing required field: {field}'})

    items = _parse_items(data.get('items'))
    if isinstance(items, str):
        return _error({'items': [items]})

    country = _clean(data, 'country', 2).upper() or HOME_COUNTRY
    if country not in COUNTRIES:
        return _error({'country': ['Choose a country from the list.']})

    name = _clean(data, 'deliver_to')
    phone = _clean(data, 'contact_number', 40)
    missing = {}
    if not name:
        missing['deliver_to'] = ['Enter the recipient’s name.']
    if not phone:
        missing['contact_number'] = ['Enter a phone number.']

    products = Product.objects.in_bulk([pid for pid, _, _ in items])
    order_items = []
    subtotal = Decimal('0')
    for pid, qty, _ in items:
        product = products.get(pid)
        if product is None or not product.is_active:
            return _error({'items': ['One of the products is no longer available.']})
        order_items.append({'product_id': pid, 'quantity': qty, 'price': product.price})
        subtotal += product.price * qty

    if country == HOME_COUNTRY:
        location_name = _clean(data, 'delivery_location')
        if not location_name:
            missing['delivery_location'] = ['Choose a delivery location.']
        if missing:
            return _error(missing)
        location = Location.objects.filter(name__iexact=location_name, is_active=True).first()
        if location is None:
            return _error({'delivery_location': ['We don’t deliver to that location. Please choose one from the list.']})
        fee = gambia_delivery_fee([products[pid] for pid, _, _ in items], location)
        order_fields = {
            'shipping_country': HOME_COUNTRY,
            'shipping_name': name,
            'shipping_phone': phone,
            'delivery_location': location.name,
            'delivery_fee': fee,
            'notes': f'Deliver to: {name}\nPhone: {phone}\nLocation: {location.name}',
        }
        return _check_expected_total(data, order_fields, order_items, subtotal + fee)

    # International: standard postal address
    address = {
        'shipping_email': _clean(data, 'email', 254),
        'shipping_address_line1': _clean(data, 'address_line1'),
        'shipping_house_number': _clean(data, 'house_number', 50),
        'shipping_address_line2': _clean(data, 'address_line2'),
        'shipping_city': _clean(data, 'city', 120),
        'shipping_region': _clean(data, 'region', 120),
        'shipping_postal_code': _clean(data, 'postal_code', 20),
        'shipping_po_box': _clean(data, 'po_box', 50),
    }
    if not address['shipping_email'] or '@' not in address['shipping_email']:
        missing['email'] = ['Enter an email address so we can send shipping updates.']
    if not address['shipping_address_line1'] and not address['shipping_po_box']:
        missing['address_line1'] = ['Enter a street address or a PO Box.']
    if not address['shipping_city']:
        missing['city'] = ['Enter a city or town.']
    if not address['shipping_postal_code'] and not address['shipping_po_box']:
        missing['postal_code'] = ['Enter a postal / ZIP code (or a PO Box).']
    if missing:
        return _error(missing)

    fee = international_shipping_fee()

    location_line = ', '.join(p for p in (address['shipping_city'], address['shipping_region'], country_name(country)) if p)
    street = ' '.join(p for p in (address['shipping_house_number'], address['shipping_address_line1']) if p)
    order_fields = {
        'shipping_country': country,
        'shipping_name': name,
        'shipping_phone': phone,
        'delivery_fee': fee,
        **address,
        'notes': '\n'.join(line for line in (
            f'Deliver to: {name}',
            f'Phone: {phone}',
            f'Location: {location_line}',
            f'Address: {street}' if street else '',
            f'Address 2: {address["shipping_address_line2"]}' if address['shipping_address_line2'] else '',
            f'PO Box: {address["shipping_po_box"]}' if address['shipping_po_box'] else '',
            f'Postal code: {address["shipping_postal_code"]}' if address['shipping_postal_code'] else '',
            f'Email: {address["shipping_email"]}',
        ) if line),
    }
    return _check_expected_total(data, order_fields, order_items, subtotal + fee)
