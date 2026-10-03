"""Shared constants for impact tracking."""
from decimal import Decimal

PLASTIC_TYPE_CHOICES = [
    ('PET', 'PET (1)'),
    ('HDPE', 'HDPE (2)'),
    ('PVC', 'PVC (3)'),
    ('LDPE', 'LDPE (4)'),
    ('PP', 'PP (5)'),
    ('PS', 'PS (6)'),
    ('MIXED', 'Mixed plastics'),
    ('OTHER', 'Other'),
]

# Average weight of a 500ml plastic bottle, used for "bottles equivalent" figures
GRAMS_PER_BOTTLE = Decimal('20')

# Order statuses at which a sale counts toward the business impact
COUNTED_ORDER_STATUSES = ('processing', 'shipped', 'delivered')

# Headline metrics can pull their value from the live tracking totals.
# key -> (label shown in admin, unit suffix)
AUTO_VALUE_CHOICES = [
    ('plastic_diverted_kg', 'Plastic diverted (kg)'),
    ('plastic_collected_kg', 'Plastic collected (kg)'),
    ('plastic_in_products_sold_kg', 'Recycled plastic in products sold (kg)'),
    ('co2_saved_kg', 'CO2 saved (kg)'),
    ('water_saved_liters', 'Water saved (liters)'),
    ('products_sold', 'Products sold'),
    ('items_produced', 'Items produced'),
    ('people_engaged', 'People engaged'),
    ('bottles_equivalent', 'Bottles equivalent'),
]

AUTO_VALUE_UNITS = {
    'plastic_diverted_kg': 'kg',
    'plastic_collected_kg': 'kg',
    'plastic_in_products_sold_kg': 'kg',
    'co2_saved_kg': 'kg',
    'water_saved_liters': 'L',
}
