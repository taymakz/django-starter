# from celery import shared_task
from django.core.management import call_command

from config.apps.messages.verification.models import VerifyOTPService
from config.libs.messaging_services.email_service import send_otp_email
from config.libs.messaging_services.phone_service import send_otp_phone


# @shared_task(name="verification_send_otp_celery", queue="tasks")
def send_otp_celery(to, code, type):
    if type == VerifyOTPService.VerifyOTPServiceTypeChoice.PHONE:
        result = send_otp_phone(to=to, code=code)
        try:
            instance = None
            if result["status"] == "OK":
                instance: VerifyOTPService = VerifyOTPService.objects.filter(to=to, code=code, type=type).order_by(
                    '-id').first()
                instance.is_sent = True

            instance.result = result
            instance.save()
        except Exception as e:
            instance: VerifyOTPService = VerifyOTPService.objects.filter(to=to, code=code, type=type).order_by(
                '-id').first()
            instance.is_sent = False
            instance.result = e
            instance.save()
    elif type == VerifyOTPService.VerifyOTPServiceTypeChoice.EMAIL:
        is_success = send_otp_email(to=to, context={"code": code})
        try:

            if is_success:
                instance: VerifyOTPService = VerifyOTPService.objects.filter(to=to, code=code, type=type).order_by(
                    '-id').first()
                instance.is_sent = True
                instance.save()
        except Exception as e:
            instance: VerifyOTPService = VerifyOTPService.objects.filter(to=to, code=code, type=type).order_by(
                '-id').first()
            instance.is_sent = False
            instance.result = e
            instance.save()


# @shared_task(name="verification_delete_expired_otp_celery", queue="tasks")
def delete_expired_otp_celery():
    call_command("delete_expired_otp")
