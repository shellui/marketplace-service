from django.core.management.base import BaseCommand

from apps.catalog.seed import seed_marketplace


class Command(BaseCommand):
    help = 'Load the Shellui Marketplace directory seed (official apps and sample community listings).'

    def handle(self, *args, **options):
        created, updated = seed_marketplace()
        self.stdout.write(f'Shellui Marketplace seed: {created} created, {updated} updated.')
