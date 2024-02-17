from random import randint

from django.db import models
from django.utils.crypto import get_random_string

from config.libs.db.models import BaseModel


class Transaction(BaseModel):
    class TransactionStatusChoice(models.TextChoices):
        SUCCESS = "پرداخت موفق"
        FAILED = "پرداخت ناموفق"
        OTHER = "نا مشخص"
        CANCEL_BY_USER = "پرداخت توسط کاربر کنسل شده است"
        WAITING = "در انتظار برای انتقال کاربر به درگاه بانک"
        RETURN_FROM_BANK = "کاربر از درگاه برگشته"
        REDIRECT_TO_BANK = "کاربر به درگاه انتقال یافت"

    user = models.ForeignKey('account.User', on_delete=models.SET_NULL, blank=True, null=True,
                             related_name='transactions')
    order = models.ForeignKey('order.Order', on_delete=models.SET_NULL, blank=True, null=True,
                              related_name='transactions')
    status = models.CharField(max_length=55, choices=TransactionStatusChoice, blank=True, null=True)
    failed_reason = models.TextField(blank=True, null=True)
    transaction_number = models.CharField(max_length=50, blank=True, null=True)  # شماره پیگیری
    slug = models.SlugField(max_length=6, unique=True, blank=True, null=True)
    ref_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'transaction'
        ordering = ('-created_at',)

    def __str__(self):
        return f"Transaction for Order - {self.get_status_display()} #{self.order_id}: {self.transaction_number}"

    def save(self, *args, **kwargs):

        if self.transaction_number is None:
            transaction_number = randint(10000000, 99999999)
            while Transaction.objects.filter(transaction_number=transaction_number).exists():
                transaction_number = randint(10000000, 99999999)
            self.transaction_number = transaction_number
        if self.slug is None:
            slug = get_random_string(6)
            while Transaction.objects.filter(slug=slug).exists():
                slug = get_random_string(6)

            self.slug = slug

        super().save(*args, **kwargs)
