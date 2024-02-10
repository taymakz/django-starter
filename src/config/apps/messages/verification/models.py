from datetime import timedelta
from random import randint

from django.db import models
from django.utils import timezone


class VerifyOTPService(models.Model):
    class VerifyOTPServiceUsageChoice(models.TextChoices):
        AUTHENTICATE = "احراز هویت"
        RESET_PASSWORD = "بازیابی کلمه عبور"
        VERIFY = "تایید"

    class VerifyOTPServiceTypeChoice(models.TextChoices):
        PHONE = "شماره موبایل"
        EMAIL = "ایمیل"

    type = models.CharField(max_length=12, choices=VerifyOTPServiceTypeChoice)
    usage = models.CharField(
        max_length=17,
        choices=VerifyOTPServiceUsageChoice,
        default=VerifyOTPServiceUsageChoice.AUTHENTICATE,
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
            self.code = randint(1000, 9999)
            self.expire_at = timezone.now() + timedelta(seconds=240)
        super().save(*args, **kwargs)

    def is_expired(self):
        now_utc = timezone.now()
        return self.expire_at < now_utc

    def send_otp(self):
        if not self.is_expired():
            pass
            # Todo: un comment on production
            # tasks.send_otp_celery.delay(to=self.to, code=self.code, type=self.type)
