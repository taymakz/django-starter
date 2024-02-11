from django.db import transaction
from django.db.models import Q, Prefetch
from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.api.enums import ResponseMessage
from config.api.response import BaseResponse
from config.apps.catalog.models import Product, ProductImage, ProductAttributeValue
from config.apps.order.models import Order, OrderItem
from config.apps.order.serializers.front import (
    OrderSerializer,
    OrderPendingSerializer,
    OrderOpenSerializer,
)


class OrderItemsValidateLocalView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        products_id = request.data.get("products_id", [])

        valid_ids = (
            Product.objects.select_related("stockrecord", "product_class")
            .only(
                "id",
                "is_public",
                "product_class__track_stock",
                "stockrecord__num_stock__gt",
            )
            .only(
                "id",
                "is_public",
                "product_class__track_stock",
                "stockrecord__num_stock",
            )
            .filter(
                Q(product_class__track_stock=True, stockrecord__num_stock__gt=0)
                | Q(product_class__track_stock=False),
                id__in=products_id,
                is_public=True,
            )
        )

        return BaseResponse(
            data=list(valid_ids),
            status=status.HTTP_204_NO_CONTENT,
            message=ResponseMessage.SUCCESS.value,
        )


class OrderGetView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get(self, request):
        try:
            with transaction.atomic():
                prefetch_images = Prefetch(
                    "product__images",
                    queryset=ProductImage.objects.all()
                    .only(
                        "id",
                        "product_id",
                        "image__file",
                        "image__width",
                        "image__height",
                    )
                    .select_related("image")
                    .prefetch_related("product__parent__images"),
                )
                prefetch_parent_images = Prefetch(
                    "product__parent__images",
                    queryset=ProductImage.objects.all()
                    .only(
                        "id",
                        "product__parent_id",
                        "image__file",
                        "image__width",
                        "image__height",
                    )
                    .select_related("image")
                    .prefetch_related("product__parent__images"),
                )

                prefetch_attributes = Prefetch(
                    "product__attribute_values",
                    queryset=ProductAttributeValue.objects.all()
                    .select_related(
                        "attribute",
                        "attribute__option_group",
                        "value_option",
                        "value_option__group",
                    )
                    .prefetch_related(
                        "value_multi_option", "value_multi_option__group"
                    ),
                )

                orders = Order.objects.prefetch_related(
                    Prefetch(
                        "items",
                        queryset=OrderItem.objects.prefetch_related(
                            prefetch_images, prefetch_attributes, prefetch_parent_images
                        )
                        .select_related(
                            "product",
                            "product__stockrecord",
                            "product__parent",
                            "product",
                            "product__product_class",
                            "product__parent__product_class",
                        )
                        .all(),
                    )
                ).filter(
                    user=request.user,
                    payment_status__in=[
                        Order.PaymentStatusChoice.OPEN_ORDER,
                        Order.PaymentStatusChoice.PENDING_PAYMENT,
                    ],
                )

                open_order = next(
                    (
                        order
                        for order in orders
                        if order.payment_status == Order.PaymentStatusChoice.OPEN_ORDER
                    ),
                    None,
                )
                pending_orders = [
                    order
                    for order in orders
                    if order.payment_status == Order.PaymentStatusChoice.PENDING_PAYMENT
                    and order.repayment_expire_at
                    and order.repayment_expire_at >= now()
                ]
                if not open_order:
                    open_order = Order.objects.create(user=request.user)

                open_order_data = OrderOpenSerializer(open_order).data
                pending_orders_data = OrderPendingSerializer(
                    pending_orders, many=True
                ).data
                result = {
                    "open_order": open_order_data,
                    "pending_orders": pending_orders_data,
                }

            return BaseResponse(
                data=result,
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value,
            )
        except Exception as e:
            print(f"apps.order.views.front line 70 : {e}")
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class OrderAddItemView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            products_id = request.data.get(
                "products_id", []
            )  # Assuming 'products_id' is a list
            order_id = request.data.get("order_id")
            # Retrieve products with is_public=True
            valid_products = (
                Product.objects.select_related("stockrecord", "product_class")
                .only(
                    "id",
                    "is_public",
                    "product_class__track_stock",
                    "stockrecord__num_stock",
                )
                .filter(
                    Q(stockrecord__num_stock__gt=0, product_class__track_stock=True)
                    | Q(product_class__track_stock=False),
                    id__in=products_id,
                    is_public=True,
                )
            )
            product_map = {product.id: product for product in valid_products}
            # Create OrderItem instances only for valid products
            order_items_to_create = [
                OrderItem(order_id=order_id, product_id=product_id, count=1)
                for product_id in products_id
                if product_id in product_map
            ]

            # Perform bulk creation
            OrderItem.objects.bulk_create(order_items_to_create)

            return BaseResponse(
                status=status.HTTP_200_OK,
                message=ResponseMessage.ORDER_ADDED_TO_CART_SUCCESSFULLY.value,
            )

        except Order.DoesNotExist:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
        except Exception as e:
            print(f"apps.order.views.front line 137 : {e}")
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class OrderItemIncreaseView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            item_id = request.data.get("item_id")
            order_item = (
                OrderItem.objects.select_related(
                    "order", "product", "product__product_class", "product__stockrecord"
                )
                .only(
                    "id",
                    "count",
                    "product__stockrecord__num_stock",
                    "product__product_class__track_stock",
                    "order__user",
                    "order__payment_status",
                )
                .get(
                    id=item_id,
                    order__user=self.request.user,
                    order__payment_status=Order.PaymentStatusChoice.OPEN_ORDER,
                )
            )
            max_allowed_count = order_item.product.stockrecord.in_order_limit
            if order_item.count >= max_allowed_count:
                return BaseResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=ResponseMessage.ORDER_ITEM_REACH_MAXIMUM_IN_ORDER_LIMIT.value.format(
                        stock=max_allowed_count
                    ),
                )
            if (
                order_item.count >= order_item.product.stockrecord.num_stock
            ) and order_item.product.product_class.track_stock:
                return BaseResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=ResponseMessage.ORDER_ITEM_DOES_NOT_EXIST_MORE_THAN.value.format(
                        stock=order_item.product.stockrecord.num_stock
                    ),
                )
            order_item.count += 1
            order_item.save()
            return BaseResponse(
                status=status.HTTP_204_NO_CONTENT,
                message=ResponseMessage.ORDER_ITEM_COUNT_INCREASED.value,
            )
        except Exception as e:
            print(f"apps.order.views.front line 192 : {e}")
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class OrderItemDecreaseView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            item_id = request.data.get("item_id")
            order_item = (
                OrderItem.objects.select_related("order")
                .only(
                    "id",
                    "count",
                    "order__user",
                    "order__payment_status",
                )
                .get(
                    id=item_id,
                    order__user=self.request.user,
                    order__payment_status=Order.PaymentStatusChoice.OPEN_ORDER,
                )
            )

            if order_item.count == 1:
                order_item.delete()
            else:
                order_item.count -= 1
                order_item.save()
            return BaseResponse(
                status=status.HTTP_204_NO_CONTENT,
                message=ResponseMessage.ORDER_ITEM_COUNT_DECREASED.value,
            )
        except Exception as e:
            print(f"apps.order.views.front line 222 : {e}")
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class OrderItemRemoveView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            item_id = request.data.get("item_id")
            OrderItem.objects.select_related("order").only(
                "id", "order__user", "order__payment_status"
            ).get(
                id=item_id,
                order__user=self.request.user,
                order__payment_status=Order.PaymentStatusChoice.OPEN_ORDER,
            ).delete()
            return BaseResponse(
                status=status.HTTP_204_NO_CONTENT,
                message=ResponseMessage.ORDER_ITEM_REMOVED.value,
            )
        except Exception as e:
            print(f"apps.order.views.front line 222 : {e}")
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
