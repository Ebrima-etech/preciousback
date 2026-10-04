"""Checkout validation for Gambian and international orders."""
from decimal import Decimal, InvalidOperation

from decouple import config
from rest_framework import status
from rest_framework.response import Response

from products.models import Product
from .countries import COUNTRIES, HOME_COUNTRY, country_name

DEFAULT_INTERNATIONAL_SHIPPING_FEE = Decimal('2500')


def international_shipping_fee():
    """Flat shipping fee (GMD) for orders outside The Gambia. Set INTERNATIONAL_SHIPPING_FEE on the server to change it."""
    try:
        return Decimal(str(config('INTERNATIONAL_SHIPPING_FEE', default=str(DEFAULT_INTERNATIONAL_SHIPPING_FEE))))
    except (InvalidOperation, ValueError):
        return DEFAULT_INTERNATIONAL_SHIPPING_FEE


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
    - The Gambia: works as before (delivery location; total as calculated by the shop page).
    - Elsewhere: full postal address; total calculated here from product prices plus international shipping.
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

    if country == HOME_COUNTRY:
        location = _clean(data, 'delivery_location')
        if not location:
            missing['delivery_location'] = ['Choose a delivery location.']
        if 'total_amount' not in data:
            missing['total_amount'] = ['Missing total.']
        if missing:
            return _error(missing)
        try:
            total = Decimal(str(data['total_amount']))
            fee = Decimal(str(data.get('delivery_fee') or 0))
        except (InvalidOperation, ValueError):
            return _error({'total_amount': ['Invalid amount.']})
        order_fields = {
            'shipping_country': HOME_COUNTRY,
            'shipping_name': name,
            'shipping_phone': phone,
            'delivery_location': location,
            'delivery_fee': fee,
            'notes': f'Deliver to: {name}\nPhone: {phone}\nLocation: {location}',
        }
        order_items = [
            {'product_id': pid, 'quantity': qty, 'price': Decimal(str(price or 0))}
            for pid, qty, price in items
        ]
        return order_fields, order_items, total

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

    # Price everything on the server for international orders
    products = Product.objects.in_bulk([pid for pid, _, _ in items])
    order_items = []
    subtotal = Decimal('0')
    for pid, qty, _ in items:
        product = products.get(pid)
        if product is None or not product.is_active:
            return _error({'items': ['One of the products is no longer available.']})
        order_items.append({'product_id': pid, 'quantity': qty, 'price': product.price})
        subtotal += product.price * qty
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
    return order_fields, order_items, subtotal + fee
