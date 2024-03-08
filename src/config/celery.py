import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.beat_schedule = {
    "delete-expired-otps-every-20-second": {
        "task": "verification_delete_expired_otp_celery",
        "schedule": crontab(minute="30", hour="3", day_of_week="1"),
    }
}

app.autodiscover_tasks()
