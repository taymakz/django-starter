from django.db import models

from config.libs.db.models import BaseModel
from config.libs.persian import province, cities


class UserAddresses(BaseModel):
    user = models.ForeignKey('account.User', on_delete=models.SET_NULL, related_name="addresses", null=True, blank=True)
    receiver_name = models.CharField(max_length=55)
    receiver_family = models.CharField(max_length=55)
    receiver_phone = models.CharField(max_length=11)
    receiver_national_code = models.CharField(max_length=12)
    receiver_province = models.CharField(max_length=100, choices=province.province)
    receiver_city = models.CharField(max_length=100, choices=cities.cities)
    receiver_postal_code = models.CharField(max_length=10)
    receiver_address = models.TextField(max_length=100)

    class Meta:
        db_table = "users_addresses"

    def __str__(self) -> str:
        return f"{self.user.username} | {self.receiver_province} | {self.receiver_city}"
