from celery import shared_task

from config.libs.messaging_services.phone_service import send_order_status_phone


@shared_task(name="send_order_status")
def send_order_status_celery(to, pattern, number, track_code):
    send_order_status_phone(to=to, pattern=pattern, number=number, track_code=track_code)
