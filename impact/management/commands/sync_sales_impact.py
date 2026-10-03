from django.core.management.base import BaseCommand

from impact.services import rebuild_sales_impact


class Command(BaseCommand):
    help = 'Create impact log entries for confirmed orders (and remove them for cancelled ones).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--refresh', action='store_true',
            help='Also recalculate existing sale entries from current product impact values.',
        )

    def handle(self, *args, **options):
        result = rebuild_sales_impact(refresh=options['refresh'])
        self.stdout.write(self.style.SUCCESS(
            f"Sales impact synced: {result['created']} created, {result['updated']} updated, {result['removed']} removed."
        ))
