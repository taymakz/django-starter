from datetime import timedelta
from random import randint

from django.db import models
from django.utils import timezone

from . import tasks
from .enums import VerificationMessageUsageOptions, VerificationMessageTypeOptions

VERIFICATION_MESSAGE_USAGE_CHOICES = [
    (data.name, data.value) for data in VerificationMessageUsageOptions
]

VERIFICATION_MESSAGE_TYPE_CHOICES = [
    (data.name, data.value) for data in VerificationMessageTypeOptions
]


class VerifyOTPService(models.Model):
    type = models.CharField(max_length=5, choices=VERIFICATION_MESSAGE_TYPE_CHOICES)
    usage = models.CharField(
        max_length=14,
        choices=VERIFICATION_MESSAGE_USAGE_CHOICES,
        default=VerificationMessageUsageOptions.AUTHENTICATE.name,
    )
    to = models.CharField(max_length=355)
    code = models.CharField(max_length=5)
    expire_at = models.DateTimeField()

    class Meta:
        db_table = "verify_otp_messages"

    def __str__(self):
        return f"{self.to} : {self.code}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.code = randint(10000, 99999)
            self.expire_at = timezone.now() + timedelta(seconds=240)
        super().save(*args, **kwargs)

    def is_expired(self):
        now_utc = timezone.now()
        return self.expire_at < now_utc

    def send_otp(self):
        if not self.is_expired():
            tasks.send_otp_celery.delay(to=self.to, code=self.code, type=self.type)
