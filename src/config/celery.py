# import os
#
# from celery import Celery
# from celery.schedules import crontab
# from kombu import Exchange, Queue
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
#
# app = Celery("config")
# app.config_from_object("django.conf:settings", namespace="CELERY")
#
# app.conf.beat_schedule = {
#     "delete-expired-otps-every-20-second": {
#         "task": "verification_delete_expired_otp_celery",
#         "schedule": crontab(minute="30", hour="3", day_of_week="1"),
#     }
# }
#
# app.conf.task_queues = [
#     Queue('tasks', Exchange('tasks'), routing_key='tasks',
#           queue_arguments={'x-max-priority': 10}),
# ]
# app.conf.task_queue_max_priority = 10
# app.conf.task_acks_late = True
# app.conf.task_default_priority = 5
# app.autodiscover_tasks()
