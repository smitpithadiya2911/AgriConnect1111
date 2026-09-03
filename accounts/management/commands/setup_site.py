from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

class Command(BaseCommand):
    help = 'Ensures the default Django Site object (SITE_ID=1) is configured for local development.'

    def handle(self, *args, **options):
        site, created = Site.objects.get_or_create(id=1, defaults={
            'domain': '127.0.0.1:8000',
            'name': 'AgriConnect Local'
        })
        if not created:
            site.domain = '127.0.0.1:8000'
            site.name = 'AgriConnect Local'
            site.save()
            self.stdout.write(self.style.SUCCESS("Updated Site (ID=1) to domain '127.0.0.1:8000'"))
        else:
            self.stdout.write(self.style.SUCCESS("Created Site (ID=1) with domain '127.0.0.1:8000'"))
