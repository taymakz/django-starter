from celery import shared_task
from django.core.management import call_command

from config.apps.messages.verification.models import VerifyOTPService
from config.libs.messaging_services.email_service import send_otp_email
from config.libs.messaging_services.phone_service import send_otp_phone


# Todo : add is Sended Field to Model,

@shared_task(name="verification_send_otp_celery")
def send_otp_celery(to, code, type):
    if type == VerifyOTPService.VerifyOTPServiceTypeChoice.PHONE:
        send_otp_phone(to=to, code=code)
    elif type == VerifyOTPService.VerifyOTPServiceTypeChoice.EMAIL:
        send_otp_email(to=to, context={code})


@shared_task(name="verification_delete_expired_otp_celery")
def delete_expired_otp_celery():
    call_command("delete_expired_otp")
