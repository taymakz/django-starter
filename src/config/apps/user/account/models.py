import uuid
from datetime import timedelta

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin, AbstractUser
from django.db import models
from django.db.models import Manager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from config.libs.db.models import BaseModel
from config.libs.validator.validators import validate_phone, validate_email


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
    class UsernameTypeChoice(models.TextChoices):
        PHONE = "شماره موبایل"
        EMAIL = "ایمیل"

    username = models.CharField(max_length=255, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(unique=True, max_length=11, blank=True, null=True)
    national_code = models.CharField(max_length=10, null=True, blank=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    is_verify = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        default_manager_name = "objects"
        db_table = "users"

    def __str__(self) -> str:
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
            if self.phone:
                self.username = self.phone
            elif self.email:
                self.username = self.email

            # Create UserPreviousDetailHistory objects for common fields
            if self.pk:
                UserPreviousDetailHistory.objects.create(
                    user=self,
                    field=UserPreviousDetailHistory.UserPreviousDetailHistoryFieldChoice.USERNAME,
                    old_value=self.__previous_username,
                    new_value=self.username,
                )  # Use updated self.username here

                # Check if email has changed
                if self.email != self.__previous_email:
                    UserPreviousDetailHistory.objects.create(
                        user=self,
                        field=UserPreviousDetailHistory.UserPreviousDetailHistoryFieldChoice.EMAIL,
                        old_value=self.__previous_email,
                        new_value=self.email,
                    )

                # Check if phone has changed
                if self.phone != self.__previous_phone:
                    UserPreviousDetailHistory.objects.create(
                        user=self,
                        field=UserPreviousDetailHistory.UserPreviousDetailHistoryFieldChoice.PHONE,
                        old_value=self.__previous_phone,
                        new_value=self.phone,
                    )

        super().save(*args, **kwargs)

    def revoke_all_tokens(self) -> None:
        for token in OutstandingToken.objects.filter(user=self).exclude(
                id__in=BlacklistedToken.objects.filter(token__user=self).values_list(
                    "token_id", flat=True
                ),
        ):
            BlacklistedToken.objects.create(token=token)

    def generate_jwt_token(self):
        refresh = RefreshToken.for_user(self)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}

    def generate_password_reset_token(self) -> str:
        self.clear_password_reset_token()
        return UserPasswordResetToken.objects.create(user=self).token

    def clear_password_reset_token(self) -> None:
        UserPasswordResetToken.objects.filter(user=self).delete()

    @staticmethod
    def get_formatted_phone(value: str) -> str:
        if User.is_phone(value):
            return (
                f"0{value}"
                if len(value) == 10 == User.UsernameTypeChoice.PHONE
                else value
            )
        else:
            raise ValueError("Invalid Phone Number.")

    @staticmethod
    def get_formatted_username(value: str) -> str:
        return f"0{value}" if validate_phone(value) and len(str(value)) == 10 else value

    @staticmethod
    def get_username_type(username: str) -> str:
        if validate_phone(username):
            return User.UsernameTypeChoice.PHONE
        elif validate_email(username):
            return User.UsernameTypeChoice.EMAIL
        else:
            raise ValueError("Invalid username type. Must be either phone or email.")

    @staticmethod
    def is_phone(value: str) -> bool:
        return True if validate_phone(value) else False

    @staticmethod
    def is_email(value: str) -> bool:
        return True if validate_email(value) else False


class RecycleUser(User):
    deleted = Manager()

    class Meta:
        proxy = True


class UserPreviousDetailHistory(BaseModel):
    class UserPreviousDetailHistoryFieldChoice(models.TextChoices):
        USERNAME = "نام کاربری"
        PHONE = "شماره موبایل"
        EMAIL = "ایمیل"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="previous_detail_histories"
    )
    field = models.CharField(
        choices=UserPreviousDetailHistoryFieldChoice, max_length=12
    )
    old_value = models.CharField(max_length=255, blank=True, null=True)
    new_value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "users_previous_detail_history"

    def __str__(self) -> str:
        return f"user : {self.user.username} changed from {self.old_value} to {self.new_value} in {self.created_at}"


class UserPasswordResetToken(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reset_password_tokens"
    )
    token = models.UUIDField(editable=False, unique=True, blank=True, null=True)

    expire_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "users_password_reset_tokens"

    def __str__(self) -> str:
        return f"user : {self.user.username} - ({self.token})"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.token = uuid.uuid4()
            self.expire_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

    def is_expired(self) -> bool:
        return self.expire_at < timezone.now()


class UserSearchHistory(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="search_histories"
    )
    search = models.CharField(max_length=255)

    class Meta:
        db_table = "users_search_history"

    def __str__(self) -> str:
        return f"{self.user} : {self.search}"


class UserFavoriteProduct(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="favorites"
    )
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="favorites"
    )

    def __str__(self):
        return f"{self.user.username} {self.product.title_ir}"

    class Meta:
        db_table = "user_favorite_product"


class UserRecentVisitedProduct(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recent_products",
    )
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="recent_products"
    )

    def __str__(self):
        return f"{self.user.username} {self.product.title_ir}"

    class Meta:
        db_table = "user_recent_visited_product"
