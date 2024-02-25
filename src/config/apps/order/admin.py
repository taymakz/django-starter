from django.contrib import admin

from config.apps.order.models import (
    Order,
    OrderItem,
    OrderAddress,
    Coupon,
    CouponUsage,
    ShippingService,
    ShippingRate,
)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # inlines = [OrderAddressInline]
    # readonly_fields = ('coupon_effect_price', 'shipping_effect_price')
    list_display = ("__str__",)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("__str__",)


@admin.register(OrderAddress)
class OrderAddressAdmin(admin.ModelAdmin):
    list_display = ("__str__",)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "code",
        "discount_type",
        "discount_amount",
        "max_usage",
        "usage_count",
    )


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = (
        "coupon",
        "user",
        "usage_count",
    )


@admin.register(ShippingService)
class ShippingServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "url",
        "is_public",
    )


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = (
        "service",
        "all_area",
        "area",
        "pay_at_destination",
        "price",
        "free_shipping_threshold",
        "is_public",
        "order",
    )
