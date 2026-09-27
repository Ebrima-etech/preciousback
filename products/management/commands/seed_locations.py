from django.core.management.base import BaseCommand
from products.models import Location
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed the database with Gambian delivery locations'

    def handle(self, *args, **options):
        locations_data = [
            {'name': 'Banjul', 'description': 'Capital city', 'default_delivery_price': Decimal('50.00')},
            {'name': 'Serekunda', 'description': 'Largest city in the Gambia', 'default_delivery_price': Decimal('45.00')},
            {'name': 'Bakau', 'description': 'Coastal town', 'default_delivery_price': Decimal('45.00')},
            {'name': 'Fajara', 'description': 'Coastal area', 'default_delivery_price': Decimal('45.00')},
            {'name': 'Kotu', 'description': 'Beach resort area', 'default_delivery_price': Decimal('45.00')},
            {'name': 'Brufut', 'description': 'Coastal settlement', 'default_delivery_price': Decimal('48.00')},
            {'name': 'Lamin', 'description': 'Village in Western Division', 'default_delivery_price': Decimal('50.00')},
            {'name': 'Gunjur', 'description': 'Southern coast town', 'default_delivery_price': Decimal('60.00')},
            {'name': 'Sanyang', 'description': 'Southern coastal area', 'default_delivery_price': Decimal('60.00')},
            {'name': 'Kartong', 'description': 'Southernmost town', 'default_delivery_price': Decimal('65.00')},
            {'name': 'Brikama', 'description': 'Major urban center', 'default_delivery_price': Decimal('55.00')},
            {'name': 'Mandinari', 'description': 'Village in Lower River Division', 'default_delivery_price': Decimal('70.00')},
            {'name': 'Kaur', 'description': 'Town in Upper River Division', 'default_delivery_price': Decimal('80.00')},
            {'name': 'Basse', 'description': 'Major town in Upper River Division', 'default_delivery_price': Decimal('90.00')},
            {'name': 'Farafenni', 'description': 'Major market town', 'default_delivery_price': Decimal('75.00')},
        ]

        created_count = 0
        updated_count = 0

        for location_data in locations_data:
            location, created = Location.objects.update_or_create(
                name=location_data['name'],
                defaults={
                    'description': location_data['description'],
                    'default_delivery_price': location_data['default_delivery_price'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created location: {location.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated location: {location.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Seeding complete! Created: {created_count}, Updated: {updated_count}')
        )
