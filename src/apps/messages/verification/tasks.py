from celery import shared_task
from django.core.management import call_command

from config.libs.messaging_services.email_service import send_otp_email
from config.libs.messaging_services.phone_service import send_otp_phone


@shared_task(name="verification_send_otp_celery")
def send_otp_celery(to, code, type):
    if type == "PHONE":
        send_otp_phone(to=to, code=code)
    elif type == "EMAIL":
        send_otp_email(to=to, context={code})


@shared_task(name="verification_delete_expired_otp_celery")
def delete_expired_otp_celery():
    call_command("delete_expired_otp")
