from django.urls import path

from config.apps.order.views import front

urlpatterns = [
    path("get/", front.OrderGetView.as_view(), name="get_user_order"),
    path(
        "validate/local/",
        front.OrderItemsValidateLocalView.as_view(),
        name="order_items_validate_local",
    ),
    path("item/add/", front.OrderAddItemView.as_view(), name="order_item_add"),
    path(
        "item/increase/",
        front.OrderItemIncreaseView.as_view(),
        name="order_item_increase",
    ),
    path(
        "item/decrease/",
        front.OrderItemDecreaseView.as_view(),
        name="order_item_decrease",
    ),
    path("item/remove/", front.OrderItemRemoveView.as_view(), name="order_item_remove"),
    path("item/clear/", front.OrderItemClearView.as_view(), name="order_item_clear"),

    path("shipping/list/", front.OrderShippingListAPIView.as_view(), name="order_shipping_list"),

    path('coupon/', front.OrderCouponUseAPIView.as_view(), name='order_coupon'),

]
