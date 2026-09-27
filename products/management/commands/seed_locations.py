from django.core.management.base import BaseCommand
from products.models import Location


class Command(BaseCommand):
    help = 'Seed Gambian delivery locations into the database'

    def handle(self, *args, **options):
        locations_data = [
            {
                'name': 'Banjul',
                'description': 'Banjul city and immediate surrounding areas'
            },
            {
                'name': 'Serekunda',
                'description': 'Serekunda and Greater Banjul area'
            },
            {
                'name': 'Bakau',
                'description': 'Bakau and coastal areas'
            },
            {
                'name': 'Fajara',
                'description': 'Fajara and residential areas'
            },
            {
                'name': 'Kotu',
                'description': 'Kotu and tourist areas'
            },
            {
                'name': 'Brufut',
                'description': 'Brufut and rural areas'
            },
            {
                'name': 'Lamin',
                'description': 'Lamin and eastern areas'
            },
            {
                'name': 'Gunjur',
                'description': 'Gunjur and southern beach areas'
            },
            {
                'name': 'Sanyang',
                'description': 'Sanyang and southern coast'
            },
            {
                'name': 'Kartong',
                'description': 'Kartong and Senegal border areas'
            },
            {
                'name': 'Brikama',
                'description': 'Brikama city and western regions'
            },
            {
                'name': 'Mandinari',
                'description': 'Mandinari and central areas'
            },
            {
                'name': 'Kaur',
                'description': 'Kaur and northern areas'
            },
            {
                'name': 'Basse',
                'description': 'Basse and eastern regions'
            },
            {
                'name': 'Farafenni',
                'description': 'Farafenni and north bank areas'
            },
        ]

        created_count = 0
        for location_data in locations_data:
            location, created = Location.objects.get_or_create(
                name=location_data['name'],
                defaults={
                    'description': location_data['description'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created location: {location.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Location already exists: {location.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {created_count} locations')
        )
