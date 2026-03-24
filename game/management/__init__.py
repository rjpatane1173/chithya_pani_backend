from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from game.models import Room


class Command(BaseCommand):
    help = 'Delete rooms older than 2 hours'

    def handle(self, *args, **kwargs):

        cutoff_time = timezone.now() - timedelta(hours=2)

        old_rooms = Room.objects.filter(created_at__lt=cutoff_time)

        count = old_rooms.count()

        old_rooms.delete()

        self.stdout.write(self.style.SUCCESS(f"Deleted {count} old rooms"))