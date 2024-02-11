from django.contrib import admin

from config.apps.order.models import Order, OrderItem, OrderAddress


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # inlines = [OrderAddressInline]
    # readonly_fields = ('coupon_effect_price', 'shipping_effect_price')
    list_display = ["__str__"]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["__str__"]


@admin.register(OrderAddress)
class OrderAddressAdmin(admin.ModelAdmin):
    list_display = ["__str__"]
