from django.core.exceptions import ObjectDoesNotExist
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
from config.apps.order.models import Order, OrderItem, ShippingRate, Coupon
from config.apps.order.serializers.front import (
    OrderSerializer,
    OrderPendingSerializer,
    OrderOpenSerializer,
    ShippingRateSerializer,
    OrderProfileSerializer,
    OrderDetailProfileSerializer,
)


class OrderItemsValidateLocalView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        products_id = request.data.get("products_id", [])

        valid_ids = (
            Product.objects.select_related(
                "stockrecord", "product_class", "parent", "parent__product_class"
            )
            .only(
                "id",
                "is_public",
                "parent__product_class__track_stock",
                "parent__stockrecord__num_stock",
                "structure",
                "product_class__track_stock",
                "stockrecord__num_stock",
            )
            .filter(
                Q(
                    Q(stockrecord__num_stock__gt=0, product_class__track_stock=True)
                    | Q(product_class__track_stock=False)
                )
                | Q(
                    Q(
                        parent__stockrecord__num_stock__gt=0,
                        parent__product_class__track_stock=True,
                    )
                    | Q(parent__product_class__track_stock=False)
                ),
                id__in=products_id,
                is_public=True,
                structure__in=[
                    Product.ProductTypeChoice.standalone,
                    Product.ProductTypeChoice.child,
                ],
            )
            .values("id")
        )
        valid_id_list = [item["id"] for item in valid_ids]
        return BaseResponse(
            data=valid_id_list,
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
                    .select_related("image", "product")
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
                    .select_related("image", "product")
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
                    None
                )
                pending_orders = next(
                    (
                        order
                        for order in orders
                        if order.payment_status == Order.PaymentStatusChoice.PENDING_PAYMENT
                           and order.repayment_expire_at
                           and order.repayment_expire_at >= now()
                    ),
                    None
                )

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
            items_to_add = request.data.get("items_to_add", [])
            order_id = request.data.get("order_id", None)
            # Assuming that User Logged in and Local Order to Remote Order

            order, _ = Order.objects.only("id", "payment_status", "lock").get_or_create(
                user=request.user,
                payment_status=Order.PaymentStatusChoice.OPEN_ORDER,
            )
            if order.lock:
                return BaseResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=ResponseMessage.FAILED.value,
                )
            if not order_id:
                order_id = order.id

            if not items_to_add:
                return BaseResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=ResponseMessage.FAILED.value,
                )
            products_id = [item["product_id"] for item in items_to_add]

            # Retrieve products with is_public=True
            valid_products = (
                Product.objects.select_related(
                    "stockrecord", "product_class", "parent", "parent__product_class"
                )
                .only(
                    "id",
                    "structure",
                    "parent__product_class__track_stock",
                    "parent__stockrecord__num_stock",
                    "is_public",
                    "product_class__track_stock",
                    "stockrecord__num_stock",
                    "stockrecord__in_order_limit",
                )
                .filter(
                    Q(
                        Q(stockrecord__num_stock__gt=0, product_class__track_stock=True)
                        | Q(product_class__track_stock=False)
                    )
                    | Q(
                        Q(
                            parent__stockrecord__num_stock__gt=0,
                            parent__product_class__track_stock=True,
                        )
                        | Q(parent__product_class__track_stock=False)
                    ),
                    id__in=products_id,
                    is_public=True,
                    structure__in=[
                        Product.ProductTypeChoice.standalone,
                        Product.ProductTypeChoice.child,
                    ],
                )
            )
            product_map = {product.id: product for product in valid_products}
            if not product_map:
                return BaseResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=ResponseMessage.FAILED.value,
                )
            # Create or get OrderItem instances and perform count validation
            for item in items_to_add:
                product_id = item["product_id"]
                count = item["count"]
                if product_id not in product_map:
                    continue  # Skip if product not valid

                # Get or create OrderItem instance
                order_item, _ = OrderItem.objects.get_or_create(
                    order_id=order_id, product_id=product_id, defaults={"count": count}
                )

                order_item.count += count if not order_item.pk else 0

                stock_record = order_item.product.stockrecord
                if stock_record:
                    stock_limit = stock_record.num_stock
                    in_order_limit = stock_record.in_order_limit

                    if in_order_limit is None:
                        # Treat in_order_limit as infinity if it's None
                        stock_limit = float("inf")
                    else:
                        stock_limit = min(stock_limit, in_order_limit)

                    if (
                            order_item.product.structure == Product.ProductTypeChoice.child
                            or order_item.product.product_class.track_stock
                    ):
                        order_item.count = min(order_item.count, stock_limit)

                order_item.save()

            return BaseResponse(
                status=status.HTTP_200_OK,
                message=ResponseMessage.ORDER_ADDED_TO_CART_SUCCESSFULLY.value,
            )

        except Order.DoesNotExist:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
        except Exception as e:
            print(f"apps.order.views.front line 298 : {e}")
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class OrderItemIncreaseView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            product_id = request.data.get("product_id")
            order_item = (
                OrderItem.objects.select_related(
                    "order", "product", "product__product_class", "product__stockrecord"
                )
                .only(
                    "id",
                    "count",
                    "product_id",
                    "product__stockrecord__num_stock",
                    "product__stockrecord__in_order_limit",
                    "product__product_class__track_stock",
                    "order__user",
                    "order__payment_status",
                    "order__lock",
                )
                .get(
                    product_id=product_id,
                    order__user=self.request.user,
                    order__payment_status=Order.PaymentStatusChoice.OPEN_ORDER,
                    order__lock=False,
                )
            )
            max_allowed_count = order_item.product.stockrecord.in_order_limit
            if max_allowed_count is None:
                max_allowed_count = float("inf")
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
            product_id = request.data.get("product_id")
            order_item = (
                OrderItem.objects.select_related("order")
                .only(
                    "id",
                    "count",
                    "product_id",
                    "order__user",
                    "order__payment_status",
                    "order__lock",
                )
                .get(
                    product_id=product_id,
                    order__user=self.request.user,
                    order__payment_status=Order.PaymentStatusChoice.OPEN_ORDER,
                    order__lock=False,
                )
            )

            if order_item.count == 1:
                order_item.delete()
                return BaseResponse(
                    status=status.HTTP_204_NO_CONTENT,
                    message=ResponseMessage.ORDER_ITEM_REMOVED.value,
                )
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

    def delete(self, request):
        try:
            product_id = request.data.get("product_id")

            OrderItem.objects.select_related("order").only(
                "id",
                "order__user",
                "order__payment_status",
                "order__lock",
                "product_id",
            ).get(
                product_id=product_id,
                order__user=self.request.user,
                order__payment_status=Order.PaymentStatusChoice.OPEN_ORDER,
                order__lock=False,
            ).delete()
            return BaseResponse(
                status=status.HTTP_204_NO_CONTENT,
                message=ResponseMessage.ORDER_ITEM_REMOVED.value,
            )
        except Exception as e:
            print(f"apps.order.views.front line 386 : {e}")
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class OrderItemClearView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            order_id = request.data.get("order_id")
            OrderItem.objects.select_related("order").filter(
                order__user=request.user,
                order__id=order_id,
                order__payment_status=Order.PaymentStatusChoice.OPEN_ORDER,
                order__lock=False,
            ).delete()
            return BaseResponse(
                status=status.HTTP_204_NO_CONTENT,
                message=ResponseMessage.ORDER_ITEM_CLEARED.value,
            )
        except Exception as e:
            print(f"apps.order.views.front line 413 : {e}")
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class OrderShippingListAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = (
            ShippingRate.objects.select_related("service", "service__image")
            .filter(is_public=True, service__is_public=True)
            .all()
        )
        serializer = ShippingRateSerializer(queryset, many=True)
        return BaseResponse(
            data=serializer.data,
            status=status.HTTP_200_OK,
            message=ResponseMessage.SUCCESS.value,
        )


class OrderCouponUseAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get("code")
        user = request.user
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return BaseResponse(
                status=status.HTTP_404_NOT_FOUND,
                message=ResponseMessage.COUPON_NOT_VALID.value,
            )
        try:
            user_current_order = Order.objects.get(
                user=user, payment_status=Order.PaymentStatusChoice.OPEN_ORDER
            )
            total_order = user_current_order.get_total_price()
            valid, message = coupon.validate_coupon(
                user_id=user.id, order_total_price=total_order
            )
            if valid:
                new_price, dif_price, percentage_effect = coupon.calculate_discount(
                    total_order
                )

                return BaseResponse(
                    data={
                        "discount_amount": dif_price,
                        "percentage_effect": percentage_effect,
                    },
                    status=status.HTTP_204_NO_CONTENT,
                    message=message,
                )
            else:
                return BaseResponse(status=status.HTTP_400_BAD_REQUEST, message=message)
        except ObjectDoesNotExist:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
        except Exception as e:
            print(f"apps.order.views.front line 467 : {e}")
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


# Profile Endpoints
class OrderGetProfileDataView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            orders = list(Order.objects.filter(
                user=request.user,
                payment_status__in=[Order.PaymentStatusChoice.PAID, Order.PaymentStatusChoice.PENDING_PAYMENT]
            ).order_by("-ordered_at"))
            all_orders = next(
                (
                    order
                    for order in orders
                    if order.payment_status == Order.PaymentStatusChoice.PAID
                ),
                None
            )
            current_orders = next(
                (
                    order
                    for order in orders
                    if order.payment_status == Order.PaymentStatusChoice.PAID and
                       order.delivery_status in [
                           Order.DeliveryStatusChoice.PENDING,
                           Order.DeliveryStatusChoice.PROCESSING,
                           Order.DeliveryStatusChoice.SHIPPED
                       ]
                ),
                None
            )
            delivered_orders = next(
                (
                    order
                    for order in orders
                    if order.payment_status == Order.PaymentStatusChoice.PAID and
                       order.delivery_status == Order.DeliveryStatusChoice.DELIVERED
                ),
                None
            )
            canceled_orders = next(
                (
                    order
                    for order in orders
                    if (
                               order.payment_status == Order.PaymentStatusChoice.PENDING_PAYMENT
                               and order.repayment_expire_at
                               and order.repayment_expire_at < now()
                       )
                       or
                       (
                               order.payment_status == Order.PaymentStatusChoice.PAID and
                               order.delivery_status == Order.DeliveryStatusChoice.CANCELED
                       )

                ),
                None
            )

            result = {
                "all_orders": OrderProfileSerializer([all_orders], many=True).data if all_orders else [],
                "current_orders": OrderProfileSerializer([current_orders], many=True).data if current_orders else [],
                "delivered_orders": OrderProfileSerializer([delivered_orders],
                                                           many=True).data if delivered_orders else [],
                "canceled_orders": OrderProfileSerializer([canceled_orders], many=True).data if canceled_orders else [],
            }
            return BaseResponse(
                data=result,
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value,
            )
        except Exception as e:
            print(f"apps.order.views.front line 536 : {e}")
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class OrderDetailProfileDataView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = OrderDetailProfileSerializer

    def get(self, request, slug=None, *args, **kwargs):
        try:
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
                .select_related("image", "product")
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
                .select_related("image", "product")
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
                .prefetch_related("value_multi_option", "value_multi_option__group"),
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
                        "product__product_class",
                        "product__parent__product_class",
                    )
                    .all(),
                )
            ).get(
                user=request.user,
                slug=slug,
                payment_status__in=[
                    Order.PaymentStatusChoice.PAID,
                    Order.PaymentStatusChoice.PENDING_PAYMENT,
                ],
            )

            data = self.serializer_class(orders).data
            return BaseResponse(
                data=data,
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value,
            )
        except Exception as e:
            print(f"apps.order.views.front line 630 : {e}")
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
