import uuid
from datetime import timedelta
from enum import Enum

from config.libs.db.models import BaseModel
from config.libs.persian import province, cities
from config.libs.validator.validators import validate_phone
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin, AbstractUser
from django.db import models
from django.db.models import Manager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken


class UserManager(BaseUserManager):
    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        if email:
            email = self.normalize_email(email)
            user = self.model(username=email, email=email, **extra_fields)
        elif phone:
            if validate_phone(phone):
                if len(phone) == 10:
                    phone = f"0{phone}"
                user = self.model(username=phone, phone=phone, **extra_fields)
            else:
                raise ValueError("Not Valid Phone Number")
        else:
            raise ValueError("Email or Phone is required to create a user.")

        if password is not None:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not phone:
            raise ValueError("Phone number is required for superuser creation")
        user = self.create_user(phone=phone, password=password, **extra_fields)
        user.save(using=self._db)
        return user


# Create your models here.
class User(BaseModel, AbstractUser):
    name = models.CharField(max_length=255, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(unique=True, max_length=11, blank=True, null=True)
    national_code = models.CharField(max_length=10, null=True, blank=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        default_manager_name = 'objects'
        db_table = "users"

    def __str__(self):
        return f"{self.username}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Save Previous fields value
        # if  changed and username was phone , email , change username too
        self.__previous_username = self.username
        self.__previous_email = self.email
        self.__previous_phone = self.phone

    def save(self, *args, **kwargs):
        if not self.pk:
            if not self.password or not self.has_usable_password():
                self.set_unusable_password()
        # Check if email or phone has changed
        if self.email != self.__previous_email or self.phone != self.__previous_phone:
            if self.phone and self.phone != self.username:
                self.username = self.phone
            elif self.email and self.email != self.username:
                self.username = self.email

            # Create UserPreviousDetailHistory objects for common fields
            if self.pk:
                UserPreviousDetailHistory.objects.create(
                    user=self,
                    field=UserInfoHistoryFields.USERNAME.name,
                    old_value=self.__previous_username,
                    new_value=self.username,
                )  # Use updated self.username here

                # Check if email has changed
                if self.email != self.__previous_email:
                    UserPreviousDetailHistory.objects.create(
                        user=self,
                        field=UserInfoHistoryFields.EMAIL.name,
                        old_value=self.__previous_email,
                        new_value=self.email,
                    )

                # Check if phone has changed
                if self.phone != self.__previous_phone:
                    UserPreviousDetailHistory.objects.create(
                        user=self,
                        field=UserInfoHistoryFields.PHONE.name,
                        old_value=self.__previous_phone,
                        new_value=self.phone,
                    )

        super().save(*args, **kwargs)

    def revoke_all_tokens(self):
        for token in OutstandingToken.objects.filter(user=self).exclude(
                id__in=BlacklistedToken.objects.filter(token__user=self).values_list('token_id', flat=True),
        ):
            BlacklistedToken.objects.create(token=token)

    def generate_jwt_token(self):
        refresh = RefreshToken.for_user(self)
        return {
            "refresh": refresh,
            "access": refresh.token
        }

    def generate_password_reset_token(self):
        self.clear_password_reset_token()
        return UserPasswordResetToken.objects.create(user=self).token

    def clear_password_reset_token(self):
        UserPasswordResetToken.objects.filter(user=self).delete()


class RecycleUser(User):
    deleted = Manager()

    class Meta:
        proxy = True


class UserInfoHistoryFields(Enum):
    USERNAME = "نام کاربری"
    PHONE = "شماره موبایل"
    EMAIL = "ایمیل"


USER_HISTORY_FIELD_CHOICES = [(data.name, data.value) for data in UserInfoHistoryFields]


class UserPreviousDetailHistory(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="previous_detail_histories"
    )
    field = models.CharField(choices=USER_HISTORY_FIELD_CHOICES, max_length=8)
    old_value = models.CharField(max_length=255)
    new_value = models.CharField(max_length=255)

    class Meta:
        db_table = "users_previous_detail_history"

    def __str__(self):
        return f"user : {self.user.username} changed from {self.old_value} to {self.new_value} in {self.created_at}"


class UserPasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(editable=False, unique=True, blank=True, null=True)

    expire_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "users_password_reset_tokens"

    def __str__(self):
        return f"user : {self.user.username} - ({self.token})"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.token = uuid.uuid4()
            self.expire_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

    def is_expired(self):
        return self.expire_at < timezone.now()


# class UserSearchHistory(models.Model):
#     user = models.ForeignKey(
#         "User", on_delete=models.CASCADE, related_name="search_histories"
#     )
#     search = models.CharField(max_length=255)
#
#     date_created = models.DateTimeField(auto_now_add=True, editable=False)
#
#     class Meta:
#         db_table = "users_search_history"
#
#     def __str__(self):
#         return f"{self.user} : {self.search}"


class UserAddresses(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    receiver_name = models.CharField(max_length=55)
    receiver_family = models.CharField(max_length=55)
    receiver_phone = models.CharField(max_length=11)
    receiver_national_code = models.CharField(max_length=12)
    receiver_province = models.CharField(max_length=100, choices=province.province)
    receiver_city = models.CharField(max_length=100, choices=cities.cities)
    receiver_postal_code = models.CharField(max_length=10)
    receiver_address = models.TextField(max_length=100)

    class Meta:
        db_table = "user_addresses"

    def __str__(self):
        return f"{self.user.username} | {self.receiver_province} | {self.receiver_city}"
