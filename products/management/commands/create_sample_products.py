from django.core.management.base import BaseCommand
from products.models import Category, Product


class Command(BaseCommand):
    help = 'Create sample products for the store'

    def handle(self, *args, **options):
        # Create categories if they don't exist
        categories_data = [
            {'name': 'Recycled Containers', 'description': 'Durable storage solutions'},
            {'name': 'Kitchenware', 'description': 'Eco-friendly kitchen tools'},
            {'name': 'Storage Solutions', 'description': 'Organize sustainably'},
            {'name': 'Eco Accessories', 'description': 'Planet-friendly items'},
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories[cat_data['name']] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {cat.name}'))

        # Create sample products
        products_data = [
            {
                'name': 'Recycled Storage Bins',
                'description': 'Durable and eco-friendly storage bins made from 100% recycled plastic. Perfect for organizing your home while helping the environment.',
                'price': '850.00',
                'stock': 15,
                'category': 'Recycled Containers',
                'image': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500&q=80',
            },
            {
                'name': 'Eco Lunch Container Set',
                'description': 'Sustainable lunch containers made from recycled plastic. Keep your meals fresh and your conscience clean with these eco-friendly containers.',
                'price': '1200.00',
                'stock': 25,
                'category': 'Kitchenware',
                'image': 'https://images.unsplash.com/photo-1578749556568-5786c4d1f70e?w=500&q=80',
            },
            {
                'name': 'Recycled Water Bottle',
                'description': 'Durable and lightweight water bottle crafted from recycled plastic. Stay hydrated while supporting sustainability.',
                'price': '750.00',
                'stock': 8,
                'category': 'Eco Accessories',
                'image': 'https://images.unsplash.com/photo-1602143407151-7e406cab6869?w=500&q=80',
            },
            {
                'name': 'Sustainable Organizers',
                'description': 'Multi-purpose organizers perfect for any space. Made from eco-friendly recycled materials to keep your space tidy and your carbon footprint low.',
                'price': '1050.00',
                'stock': 20,
                'category': 'Storage Solutions',
                'image': 'https://images.unsplash.com/photo-1542286455-85b6079d5587?w=500&q=80',
            },
            {
                'name': 'Eco Dish Brush Set',
                'description': 'Sustainable dish brushes made from recycled bristles. An effective and environmentally responsible choice for your kitchen.',
                'price': '450.00',
                'stock': 30,
                'category': 'Kitchenware',
                'image': 'https://images.unsplash.com/photo-1584854884173-1f57b9a7ba14?w=500&q=80',
            },
            {
                'name': 'Recycled Desk Organizer',
                'description': 'Keep your workspace organized with this stylish desk organizer made from 100% recycled plastic.',
                'price': '650.00',
                'stock': 18,
                'category': 'Storage Solutions',
                'image': 'https://images.unsplash.com/photo-1589939705066-5470d59623ca?w=500&q=80',
            },
            {
                'name': 'Eco Plant Pot',
                'description': 'Beautiful and sustainable plant pot perfect for any home or office. Support green living with this eco-friendly planter.',
                'price': '550.00',
                'stock': 22,
                'category': 'Eco Accessories',
                'image': 'https://images.unsplash.com/photo-1578500494198-246f612d03b3?w=500&q=80',
            },
            {
                'name': 'Recycled Trash Bin',
                'description': 'Stylish and functional trash bin made from recycled materials. Perfect for any room while promoting sustainability.',
                'price': '920.00',
                'stock': 12,
                'category': 'Recycled Containers',
                'image': 'https://images.unsplash.com/photo-1595430774223-ef52624120d2?w=500&q=80',
            },
        ]

        for prod_data in products_data:
            category = categories[prod_data.pop('category')]
            prod, created = Product.objects.get_or_create(
                name=prod_data['name'],
                defaults={
                    **prod_data,
                    'category': category,
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created product: {prod.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Product already exists: {prod.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully created sample products!'))
