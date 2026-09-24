from django.core.management.base import BaseCommand
from cms.models import HeroSlide, Service, TeamMember, Partner


class Command(BaseCommand):
    help = 'Seed website content from hardcoded data'

    def handle(self, *args, **options):
        self.stdout.write('Starting to seed website content...')

        # Seed Hero Slides
        self.seed_hero_slides()

        # Update Services
        self.seed_services()

        # Seed Team Members
        self.seed_team_members()

        # Seed Partners
        self.seed_partners()

        self.stdout.write(self.style.SUCCESS('Successfully seeded all website content!'))

    def seed_hero_slides(self):
        hero_slides = [
            {
                'title': 'From Pollution to Solution',
                'description': 'Join our mission to transform plastic waste into valuable products',
                'image_url': 'https://res.cloudinary.com/divk8m0ff/image/upload/v1789311020/WhatsApp_Image_2026-09-13_at_10.04.14_4_gksbhh.jpg',
                'slide_type': 'description',
                'show_badge': True,
                'show_heading': False,
                'show_buttons': True,
                'show_description': True,
                'order': 0,
            },
            {
                'title': 'From Pollution to Solution',
                'description': 'Transforming plastic waste into valuable, sustainable products',
                'image_url': 'https://res.cloudinary.com/divk8m0ff/image/upload/v1789310801/WhatsApp_Image_2026-09-13_at_10.04.16_2_l3izsj.jpg',
                'slide_type': 'main',
                'show_badge': True,
                'show_heading': True,
                'show_buttons': True,
                'show_description': False,
                'order': 1,
            },
            {
                'title': 'Community Impact',
                'description': 'Building better futures together with sustainable solutions',
                'image_url': 'https://res.cloudinary.com/divk8m0ff/image/upload/v1789311068/WhatsApp_Image_2026-09-13_at_10.04.13_jj8pfj.jpg',
                'slide_type': 'description',
                'show_badge': True,
                'show_heading': False,
                'show_buttons': True,
                'show_description': True,
                'order': 2,
            },
        ]

        for slide_data in hero_slides:
            HeroSlide.objects.get_or_create(
                image_url=slide_data['image_url'],
                defaults=slide_data
            )
        self.stdout.write(self.style.SUCCESS(f'✓ Seeded {len(hero_slides)} hero slides'))

    def seed_services(self):
        services = [
            {
                'name': 'Collections',
                'description': 'Community-driven plastic collection programs to reduce environmental waste.',
                'icon': 'GiRecycle',
                'color_from': 'blue-500',
                'color_to': 'blue-600',
                'order': 0,
                'is_active': True,
            },
            {
                'name': 'Recycling',
                'description': 'Advanced processing and recycling of plastic waste into quality products.',
                'icon': 'BiRecycle',
                'color_from': 'emerald-500',
                'color_to': 'emerald-600',
                'order': 1,
                'is_active': True,
            },
            {
                'name': 'Workshops',
                'description': 'Educational programs and hands-on training in sustainable practices.',
                'icon': 'MdSchool',
                'color_from': 'amber-500',
                'color_to': 'amber-600',
                'order': 2,
                'is_active': True,
            },
        ]

        for service_data in services:
            Service.objects.get_or_create(
                name=service_data['name'],
                defaults=service_data
            )
        self.stdout.write(self.style.SUCCESS(f'✓ Seeded {len(services)} services'))

    def seed_team_members(self):
        team_members = [
            {
                'name': 'Baai E Jaabang',
                'role': 'Co-Founder',
                'description': 'Co-founder of Precious Plastic Gambia and Executive Director of the Trust Agency for Rural Development, Baai is deeply committed to environmental enhancement. He works passionately to create a greener, healthier Gambia, driving sustainable development and community-led solutions to eliminate plastic waste pollution.',
                'order': 0,
                'is_active': True,
            },
            {
                'name': 'Alieu Sowe',
                'role': 'Co-Founder',
                'description': 'Co-founder of Precious Plastic Gambia and Founder & CEO of Plastic Recycling Gambia LTD, Alieu brings entrepreneurial leadership to the circular economy. Driven by a passion for environmental protection, he works to advance sustainable waste management solutions and build a cleaner Gambia free from plastic pollution diverting tons of discarded plastics from waste to wealth.',
                'order': 1,
                'is_active': True,
            },
            {
                'name': 'Rebecca Talbot',
                'role': 'Co-Founder',
                'description': 'Co-founder of Precious Plastic Gambia and Founder of Growing Green Communities, Rebecca is dedicated to environmental enhancement and grassroots sustainability. She works passionately to empower communities, eliminate plastic waste, and cultivate a greener, healthier environment across The Gambia and beyond.',
                'order': 2,
                'is_active': True,
            },
            {
                'name': 'Babucarr E Camara',
                'role': 'Co-Founder & Operations Manager',
                'description': 'Co-founder and Operations Manager at Precious Plastic Gambia, Babucarr leads strategic operations to turn plastic waste into value. Passionate about environmental enhancement, he combines operational leadership with a strong vision for a cleaner, healthier Gambia free from plastic pollution.',
                'image_url': '/team/Babucarr E Camara.jpg',
                'order': 3,
                'is_active': True,
            },
            {
                'name': 'Omar Manjang',
                'role': 'Machine Operator & Furniture Builder',
                'description': 'Driven by a deep passion for environmental protection and recycling, Omar operates plastic recycling machinery to transform waste into durable furniture and handcrafted jewelry. In his role, he crafts sustainable products and supports production workflow to advance Precious Plastic Gambia\'s circular economy mission.',
                'image_url': '/team/Omar Manjang.jpg',
                'order': 4,
                'is_active': True,
            },
            {
                'name': 'Mariama M Jabang',
                'role': 'Operations & Store Associate',
                'description': 'Passionate about Precious Plastic Gambia\'s mission, Mariama brings her best every day to ensure team objectives are met. She operates the shredder and injection machine to make handcrafted jewelry, while managing sales records and keeping the shop organized.',
                'image_url': '/team/mariama m jabang.jpg',
                'order': 5,
                'is_active': True,
            },
            {
                'name': 'Ramatoulie Manneh',
                'role': 'Machine Operator & Artisan',
                'description': 'Dedicated and reliable, Ramatoulie brings strong punctuality and a genuine passion for her work every day. Operating plastic recycling machinery, she plays a vital role in transforming waste into beautifully crafted jewelry and durable furniture, helping advance Precious Plastic Gambia\'s commitment to environmental sustainability.',
                'image_url': '/team/Ramatoulie Manneh.jpg',
                'order': 6,
                'is_active': True,
            },
            {
                'name': 'Bakary Saidy',
                'role': 'Support Staff',
                'description': 'Always ready to step in where needed, Bakary supports core operations by running recycling machinery, building durable furniture, and crafting jewelry. He also operates mobility equipment to assist with plastic collection efforts, driving Precious Plastic Gambia\'s sustainability goals forward.',
                'image_url': '/team/Bakary Saidy.jpg',
                'order': 7,
                'is_active': True,
            },
            {
                'name': 'Sheriffo Manneh',
                'role': 'Support Staff',
                'description': 'A versatile team player, Sheriffo provides crucial operational support through machine operation, furniture fabrication, and jewelry making. He actively assists with plastic collection transport, ensuring smooth daily workflows and contributing to Precious Plastic Gambia\'s circular economy mission.',
                'image_url': '/team/Sheriffo Manjang.jpg',
                'order': 8,
                'is_active': True,
            },
        ]

        for member_data in team_members:
            TeamMember.objects.get_or_create(
                name=member_data['name'],
                defaults=member_data
            )
        self.stdout.write(self.style.SUCCESS(f'✓ Seeded {len(team_members)} team members'))

    def seed_partners(self):
        partners = [
            {
                'name': 'Partner 1',
                'logo_url': 'https://images.pexels.com/photos/3962286/pexels-photo-3962286.jpeg?w=150&h=80&fit=crop',
                'order': 0,
            },
            {
                'name': 'Partner 2',
                'logo_url': 'https://images.pexels.com/photos/5830900/pexels-photo-5830900.jpeg?w=150&h=80&fit=crop',
                'order': 1,
            },
            {
                'name': 'Partner 3',
                'logo_url': 'https://images.pexels.com/photos/5632399/pexels-photo-5632399.jpeg?w=150&h=80&fit=crop',
                'order': 2,
            },
            {
                'name': 'Partner 4',
                'logo_url': 'https://images.pexels.com/photos/6474056/pexels-photo-6474056.jpeg?w=150&h=80&fit=crop',
                'order': 3,
            },
            {
                'name': 'Partner 5',
                'logo_url': 'https://images.pexels.com/photos/3962286/pexels-photo-3962286.jpeg?w=150&h=80&fit=crop',
                'order': 4,
            },
        ]

        for partner_data in partners:
            Partner.objects.get_or_create(
                name=partner_data['name'],
                defaults=partner_data
            )
        self.stdout.write(self.style.SUCCESS(f'✓ Seeded {len(partners)} partners'))
