from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from config import settings


def send_otp_email(
        to, context, template_name="emails/email_otp.html", subject="تیپوش | کد تایید"
):
    try:
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)

        from_email = settings.EMAIL_HOST_FROM_ADDRESS
        send_mail(
            subject,
            plain_message,
            from_email,
            [to],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(e)
