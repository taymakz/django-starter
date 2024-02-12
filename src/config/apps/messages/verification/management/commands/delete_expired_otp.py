from django.core.management.base import BaseCommand
from django.utils import timezone

from config.apps.messages.verification.models import VerifyOTPService


class Command(BaseCommand):
    help = "Remove all expired VerifyOTPService objects"

    def handle(self, *args, **options):
        now_utc = timezone.now()
        expired_objects = VerifyOTPService.objects.filter(expire_at__lt=now_utc)

        count = expired_objects.count()
        expired_objects.delete()

        self.stdout.write(
            self.style.SUCCESS(f"Successfully removed {count} expired objects.")
        )
