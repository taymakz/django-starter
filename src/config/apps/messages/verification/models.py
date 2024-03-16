from datetime import timedelta
from random import randint

from django.db import models
from django.utils import timezone


class VerifyOTPService(models.Model):
    class VerifyOTPServiceUsageChoice(models.TextChoices):
        AUTHENTICATE = "AUTHENTICATE"
        RESET_PASSWORD = "RESET_PASSWORD"
        VERIFY = "VERIFY"

    class VerifyOTPServiceTypeChoice(models.TextChoices):
        PHONE = "PHONE"
        EMAIL = "EMAIL"

    type = models.CharField(max_length=12, choices=VerifyOTPServiceTypeChoice)
    usage = models.CharField(
        max_length=17,
        choices=VerifyOTPServiceUsageChoice,
        default=VerifyOTPServiceUsageChoice.AUTHENTICATE,
    )
    to = models.CharField(max_length=355)
    code = models.CharField(max_length=5)
    is_sent = models.BooleanField(default=False)
    result = models.TextField(null=True, blank=True)
    expire_at = models.DateTimeField()

    class Meta:
        db_table = "verify_otp_messages"

    def __str__(self):
        return f"{self.to} : {self.code}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.code = randint(1000, 9999)
            self.expire_at = timezone.now() + timedelta(seconds=240)
        super().save(*args, **kwargs)

    def is_expired(self):
        now_utc = timezone.now()
        return self.expire_at < now_utc

    def send_otp(self):
        if not self.is_expired():
            from config.apps.messages.verification import tasks
            tasks.send_otp_celery.apply_async(kwargs={"to": self.to, "code": self.code, "type": self.type}, priority=10)
