from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils.timezone import now

from config.api.enums import ResponseMessage
from config.apps.user.address.models import UserAddresses
from config.libs.db.models import BaseModel
from config.libs.persian.province import province


class Order(BaseModel):
    class DeliveryStatusChoice(models.TextChoices):
        CANCELED = "لغو شده"
        PENDING = "در انتظار تایید"
        PROCESSING = "درحال پردازش"
        SHIPPED = "ارسال شده"
        DELIVERED = "تحویل داده شده"

    class PaymentStatusChoice(models.TextChoices):
        OPEN_ORDER = "باز"
        PENDING_PAYMENT = "در انتظار پرداخت"
        PAID = "پرداخت شده"

    user = models.ForeignKey(
        "account.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    slug = models.SlugField(
        max_length=5, unique=True, blank=True, null=True
    )  # order number

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatusChoice,
        default=PaymentStatusChoice.OPEN_ORDER,
    )
    lock_modify_until = models.DateTimeField(null=True, blank=True)  # use for payment
    repayment_expire_at = models.DateTimeField(blank=True, null=True)

    delivery_status = models.CharField(
        max_length=20, choices=DeliveryStatusChoice, blank=True, null=True
    )
    delivery_canceled_reason = models.CharField(max_length=255, blank=True, null=True)

    shipping_rate = models.ForeignKey(
        "ShippingRate",
        on_delete=models.SET_NULL,
        related_name="orders",
        blank=True,
        null=True,
    )
    address = models.OneToOneField(
        "OrderAddress",
        on_delete=models.SET_NULL,
        related_name="order",
        blank=True,
        null=True,
    )

    coupon = models.ForeignKey(
        "Coupon",
        on_delete=models.SET_NULL,
        related_name="orders",
        blank=True,
        null=True,
    )

    # Fields that Fill After Payment
    tracking_code = models.CharField(
        max_length=40, blank=True, null=True
    )  # کد رهگیری از طرف شرکت پست

    delivery_status_modified_at = models.DateTimeField(blank=True, null=True)
    ordered_at = models.DateTimeField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    final_paid_price = models.PositiveBigIntegerField(default=0)  # مبلغ پرداختی نهایی
    final_profit_price = models.PositiveBigIntegerField(default=0)  # سود نهایی
    final_total_items_final_price = models.PositiveBigIntegerField(
        default=0
    )  # قیمت نهایی محصولات سبد خرید
    final_total_items_before_discount_price = models.PositiveBigIntegerField(
        default=0
    )  # قیمت قبل تخفیف محصولات سبد خرید

    final_coupon_effect_price = models.PositiveBigIntegerField(
        default=0
    )  # تاثیر کد تخفیف بعد خرید
    final_shipping_effect_price = models.PositiveBigIntegerField(
        default=0
    )  # هزینه ارسال بعد خرید

    class Meta:
        db_table = "order"
        ordering = ["-ordered_at"]

    def __str__(self):
        return (
            f"{self.user.email} - {self.user.phone} Count : ( {self.items.count()} ) : "
            f"( {self.get_payment_status_display()} ) : ( {self.get_delivery_status_display()} ) "
        )

    def get_absolute_url(self):
        return f"/panel/orders/{self.slug}"

    def set_repayment_expire_date(self):
        self.repayment_expire_at = now() + timedelta(hours=1)
        self.save()

    def is_paid(self):
        return self.payment_status == Order.PaymentStatusChoice.PAID

    @staticmethod
    def generate_unique_slug():
        import random

        while True:
            slug = str(random.randint(10000, 99999))
            if not Order.objects.filter(slug=slug).exists():
                return slug

    @staticmethod
    def is_valid_shipping_method(user_address: UserAddresses, shipping: "ShippingRate"):
        # Get the ShippingPrice object with the given ID
        if not user_address or not shipping:
            return False, "آدرس و یا شیوه ارسال نا معتبر"
        if shipping.all_area:
            # Filter all ShippingPrice objects that are active and not equal to 'همه'
            other_shipping_areas = ShippingRate.objects.filter(
                all_area=True, is_active=True
            )
            if user_address and user_address.receiver_province in [
                shipping_area.area for shipping_area in other_shipping_areas
            ]:
                # User's main address province matches an active shipping area
                message = ResponseMessage.PAYMENT_NOT_VALID_SELECTED_SHIPPING.value
                return False, message
            else:
                return True, None
        else:
            if user_address and user_address.receiver_province == shipping.area:
                # User's main address province matches the shipping area
                return True, None
            else:
                message = ResponseMessage.PAYMENT_NOT_VALID_SELECTED_SHIPPING.value
                return False, message

    def get_total_price(self):  # before coupon
        return sum(item.get_total_price() for item in self.items.all())

    def get_payment_price(self):
        return self.get_total_price() + self.shipping_rate.calculate_price(
            order_price=self.get_total_price()
        )


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="in_baskets"
    )
    count = models.PositiveSmallIntegerField(default=0)

    # Fields that Fill After Payment
    final_price = models.PositiveBigIntegerField(null=True, blank=True, editable=False)
    final_price_before_discount = models.PositiveBigIntegerField(
        null=True, blank=True, editable=False
    )
    final_discount = models.PositiveBigIntegerField(
        null=True, blank=True, editable=False
    )
    final_profit = models.PositiveBigIntegerField(null=True, blank=True, editable=False)

    class Meta:
        db_table = "order_item"

    def __str__(self):
        return (
            f"{self.order.user.email} - {self.order.user.phone} "
            f"- {self.product.title_ir}"
        )

    def get_total_price(self):
        return self.product.stockrecord.final_price * self.count

    def get_total_price_before_discount(self):
        return self.product.stockrecord.sale_price

    def get_total_profit(self):
        if self.product.stockrecord.special_sale_price:
            return (
                self.product.stockrecord.sale_price
                - self.product.stockrecord.special_sale_price
            )
        return 0

    def get_total_diff_price(self):
        if self.product.stockrecord.special_sale_price:
            return self.product.stockrecord.sale_price
        return 0

    def set_final_price(self):
        self.final_price = self.get_total_price()
        self.final_price_before_discount = self.get_total_price_before_discount()
        self.final_discount = self.get_total_diff_price()
        self.final_profit = self.get_total_profit()
        self.save()


class OrderAddress(models.Model):
    receiver_fullname = models.CharField(max_length=100)
    receiver_phone = models.CharField(max_length=11)
    receiver_city = models.CharField(max_length=100)
    receiver_province = models.CharField(max_length=100)
    receiver_postal_code = models.CharField(max_length=100)
    receiver_address = models.CharField(max_length=300)
    receiver_national_code = models.CharField(max_length=11)

    class Meta:
        db_table = "order_address"


class Coupon(BaseModel):
    title = models.CharField(max_length=60, null=True, blank=True)
    code = models.CharField(
        max_length=50,
        unique=True,
        validators=[
            RegexValidator(
                r"^[a-zA-Z0-9]*$", "Only alphanumeric characters are allowed."
            )
        ],
    )
    discount_type = models.CharField(
        max_length=1, choices=[("%", "Percentage"), ("$", "Fixed amount")]
    )

    discount_amount = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    max_usage = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(1),
        ],
    )
    usage_count = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    max_usage_per_user = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(1),
        ],
    )
    min_order_total = models.PositiveIntegerField(
        blank=True, null=True, validators=[MinValueValidator(0)]
    )
    max_order_total = models.PositiveIntegerField(
        blank=True, null=True, validators=[MinValueValidator(0)]
    )
    only_first_order = models.BooleanField(default=False)

    only_categories = models.ManyToManyField("catalog.Category")
    only_products = models.ManyToManyField("catalog.Product")
    only_brands = models.ManyToManyField("catalog.Brand")
    only_users = models.ManyToManyField("account.User")

    start_at = models.DateTimeField(blank=True, null=True)
    expire_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "coupon"
        ordering = ("-created_at",)

    def __str__(self):
        return f"[ {self.code} ] {self.discount_amount:,}{self.discount_type} (usage : {self.coupon_usages.count()})"

    def calculate_discount(self, price):
        if self.discount_type == "%":
            discount = int(round(price * (self.discount_amount / 100)))
            percentage_effect = self.discount_amount
        else:
            discount = int(min(self.discount_amount, price))
            percentage_effect = (discount / price) * 100

        discounted_price = int(price - discount)
        discount_difference = int(price - discounted_price)
        return discounted_price, discount_difference, int(percentage_effect)

    def clean(self):
        super().clean()
        if (
            self.min_order_total is not None
            and self.max_order_total is not None
            and self.min_order_total > self.max_order_total
        ):
            raise ValidationError(
                "Minimum order total cannot be greater than maximum order total."
            )
        if (
            self.expire_at is not None
            and self.start_at is not None
            and self.expire_at <= self.start_at
        ):
            raise ValidationError("expire date must be after start date.")

    def validate_coupon(self, order_total_price, user_id):
        # TODO : validation for only_categories  only_products  only_brands  only_users

        if self.max_usage is not None and self.max_usage <= self.usage_count:
            return False, "کد تخفیف به حداکثر حد مجاز استفاده رسیده است"
        if self.max_usage_per_user is not None:
            from config.apps.user.account.models import User

            user = User.objects.filter(id=user_id).first()
            coupon_usage = CouponUsage.objects.filter(coupon=self, user=user).first()
            if (
                coupon_usage is not None
                and coupon_usage.usage_count >= self.max_usage_per_user
            ):
                return (
                    False,
                    f"کد تخفیف وارد شده فقط {self.max_usage_per_user} بار  قابل استفاده برای هر کاربری میباشد",
                )
        if self.expire_at is not None and self.expire_at <= now():
            return False, "کد تخفیف معتبر نمیباشد"
        if (
            self.min_order_total is not None
            and order_total_price < self.min_order_total
        ):
            return (
                False,
                f"کد تخفیف وارد شده قابل استفاده برای سفارش های بیشتر از {self.min_order_total:,} می باشد",
            )
        if (
            self.max_order_total is not None
            and order_total_price > self.max_order_total
        ):
            return (
                False,
                f"کد تخفیف وارد شده قابل استفاده برای سفارش های کمتر از {self.max_order_total:,} می یباشد",
            )

        if self.start_at is not None and now() < self.start_at:
            return False, "کد تخفیف معتبر نمیباشد"

        if self.expire_at is not None and now() > self.expire_at:
            return False, f"کد تخفیف وارد شده منقضی شده است"

        if self.only_first_order:
            if Order.objects.filter(
                user_id=user_id, payment_status=Order.PaymentStatusChoice.PAID
            ).exists():
                return False, "کد تخفیف فقط برای اولین خرید قابل استفاده است"

        return True, "کد تخفیف با موفقیت اعمال شد"


class CouponUsage(models.Model):
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coupon_usages",
    )
    user = models.ForeignKey(
        "account.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coupon_usages",
    )
    usage_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "coupon_usage"


class ShippingService(BaseModel):
    image = models.ForeignKey(
        "media.Media",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="shipping_services",
    )
    name = models.CharField(max_length=115)
    url = models.URLField(blank=True, null=True)
    is_public = models.BooleanField(default=False)

    class Meta:
        db_table = "shipping_service"

    def __str__(self):
        return f"{self.name} : {self.url}"


class ShippingRate(BaseModel):
    service = models.ForeignKey(
        ShippingService, on_delete=models.CASCADE, related_name="shipping_rates"
    )
    all_area = models.BooleanField(default=False)
    area = models.CharField(max_length=24, choices=province, null=True, blank=True)
    pay_at_destination = models.BooleanField(default=False)
    price = models.PositiveIntegerField(null=True, blank=True, default=0)
    free_shipping_threshold = models.PositiveIntegerField(
        null=True, blank=True, default=0
    )

    is_public = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0, blank=True, null=True)

    class Meta:
        db_table = "shipping_rate"
        ordering = ("order",)
        unique_together = [
            ("service", "area", "is_public"),
            ("service", "all_area", "is_public"),
        ]

    def __str__(self):
        return (
            f"{self.service.name} ( {self.area} ): {self.price:,} "
            f"- رایگان بالای : {self.free_shipping_threshold:,}"
        )

    def calculate_price(self, order_price):
        return (
            0
            if self.pay_at_destination
            or (
                self.free_shipping_threshold
                and order_price > self.free_shipping_threshold
            )
            else self.price
        )