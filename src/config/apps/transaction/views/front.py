import json
from datetime import timedelta

import requests
from django.conf import settings
from django.db.models import Prefetch
from django.shortcuts import redirect
from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.api.enums import ResponseMessage
from config.api.response import BaseResponse
from config.apps.catalog.models import Product
from config.apps.order.models import (
    Order,
    ShippingRate,
    OrderAddress,
    Coupon,
    OrderItem,
)
from config.apps.transaction.models import Transaction
from config.apps.user.address.models import UserAddresses


class TransactionResult(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, transaction_number, transaction_slug):
        try:
            # Filter the Transaction model based on the provided criteria
            transaction = Transaction.objects.select_related("order").get(
                transaction_number=transaction_number,
                slug=transaction_slug,
                created_at__gte=(now() - timedelta(hours=1)),
            )
            order = transaction.order
            # Prepare the CheckoutResultDTO
            result = {
                "transaction_status": transaction.status,
                "transaction_number": transaction.transaction_number,
                "order_slug": order.slug if order else None,
                "payment_date": transaction.created_at,
                "repayment_expire_at": order.repayment_expire_at,
                "is_repayment_expired": bool(
                    order
                    and order.repayment_expire_at
                    and order.repayment_expire_at < now()
                ),
            }

            return BaseResponse(data=result, status=status.HTTP_200_OK)
        except Transaction.DoesNotExist:
            return BaseResponse(status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"exception on transacction.views.front line 63 : {e}")
            return BaseResponse(status=status.HTTP_404_NOT_FOUND)


class TransactionRequest(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        try:

            current_order: Order = (
                Order.objects.prefetch_related(
                    Prefetch(
                        "items",
                        queryset=OrderItem.objects.select_related(
                            "product",
                            "product__product_class",
                            "product__parent__product_class",
                            "product__stockrecord",
                        ),
                    )
                )
                .select_related("shipping_rate", "address")
                .get(
                    user=user,
                    payment_status=Order.PaymentStatusChoice.OPEN_ORDER,
                    lock=False,
                )
            )
            current_order.lock = True
            current_order.save()

        except Order.DoesNotExist:
            return BaseResponse(
                data={"redirect_to": "/checkout/cart/"},
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.FAILED.value,
            )

        if current_order.items.count() == 0:
            current_order.lock = False
            current_order.save()
            return BaseResponse(
                data={"redirect_to": "/checkout/cart/"},
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.FAILED.value,
            )

        address = request.data.get("address", None)
        shipping = request.data.get("shipping", None)

        if not address or not shipping:
            current_order.lock = False
            current_order.save()
            return BaseResponse(
                data={"redirect_to": "/checkout/shipping/"},
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.FAILED.value,
            )

        try:
            selected_shipping = ShippingRate.objects.get(
                id=shipping["id"], is_public=True
            )
            selected_address = UserAddresses.objects.get(user=user, id=address["id"])
        except (ShippingRate.DoesNotExist, UserAddresses.DoesNotExist):
            current_order.lock = False
            current_order.save()
            return BaseResponse(
                data={"redirect_to": "/checkout/shipping/"},
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.PAYMENT_NOT_VALID_SELECTED_SHIPPING_OR_ADDRESS.value,
            )

        # Validate Address and Shipping Service
        is_valid_shipping, shipping_validate_message = (
            current_order.is_valid_shipping_method(
                user_address=selected_address, shipping=selected_shipping
            )
        )

        if not is_valid_shipping:
            current_order.lock = False
            current_order.save()
            return BaseResponse(
                data={"redirect_to": "/checkout/shipping/"},
                status=status.HTTP_400_BAD_REQUEST,
                message=shipping_validate_message,
            )

        if current_order.address:
            # Update the existing address instead of deleting it
            current_order.address.receiver_name = selected_address.receiver_name
            current_order.address.receiver_family = selected_address.receiver_family
            current_order.address.receiver_phone = selected_address.receiver_phone
            current_order.address.receiver_city = selected_address.receiver_city
            current_order.address.receiver_province = selected_address.receiver_province
            current_order.address.receiver_postal_code = (
                selected_address.receiver_postal_code
            )
            current_order.address.receiver_building_number = (
                selected_address.receiver_building_number
            )
            current_order.address.receiver_unit = selected_address.receiver_unit
            current_order.address.receiver_address = selected_address.receiver_address
            current_order.address.save()
        else:
            # Create a new address if the current_order doesn't have one
            order_address = OrderAddress.objects.create(
                receiver_name=selected_address.receiver_name,
                receiver_phone=selected_address.receiver_phone,
                receiver_city=selected_address.receiver_city,
                receiver_province=selected_address.receiver_province,
                receiver_postal_code=selected_address.receiver_postal_code,
                receiver_building_number=selected_address.receiver_building_number,
                receiver_unit=selected_address.receiver_unit,
                receiver_address=selected_address.receiver_address,
            )
            current_order.address = order_address

        current_order.shipping_rate = selected_shipping
        current_order.save()
        # Address and Shipping are Valid.
        coupon_code = request.data.get("coupon", None)

        order_total_price = order_total_price_before_coupon = (
            current_order.get_total_price()
        )
        order_shipping_effect_price = current_order.shipping_rate.calculate_price(
            order_price=order_total_price_before_coupon
        )
        order_total_price += order_shipping_effect_price
        # check if user Used Coupon is Exist And Valid Or Raise Error
        coupon_effect_dif_price = 0
        if coupon_code:
            try:
                used_coupon = Coupon.objects.get(code=coupon_code)
            except Coupon.DoesNotExist:
                current_order.lock = False
                current_order.save()
                return BaseResponse(
                    data={"redirect_to": "/checkout/shipping/"},
                    status=status.HTTP_400_BAD_REQUEST,
                    message=ResponseMessage.PAYMENT_NOT_VALID_USED_COUPON.value,
                )
            is_valid_coupon, coupon_validate_message = used_coupon.validate_coupon(
                user_id=user.id, order_total_price=order_total_price
            )

            if not is_valid_coupon:
                current_order.lock = False
                current_order.save()
                return BaseResponse(
                    data={"redirect_to": "/checkout/shipping/"},
                    status=status.HTTP_400_BAD_REQUEST,
                    message=coupon_validate_message,
                )
            coupon_effect_new_price, coupon_effect_dif_price, percentage_effect = (
                used_coupon.calculate_discount(order_total_price)
            )
            order_total_price -= coupon_effect_dif_price
        # Coupon Checked.
        # if order is free
        if order_total_price == 0:

            current_order.payment_status = Order.PaymentStatusChoice.PAID
            current_order.delivery_status = Order.DeliveryStatusChoice.PENDING

            current_order.final_paid_price = order_total_price

            current_order.final_profit_price = current_order.get_total_profit_price()

            current_order.final_total_items_final_price = current_order.get_total_items_final_price()

            current_order.final_total_items_before_discount_price = current_order.get_total_items_before_discount_price()

            current_order.final_coupon_effect_price = coupon_effect_dif_price
            current_order.final_shipping_effect_price = order_shipping_effect_price
            current_order.ordered_at = now()
            current_order.delivery_status_modified_at = now()
            for item in current_order.items.all():
                # child Product
                if item.product.structure == Product.ProductTypeChoice.child:
                    if item.product.parent.product_class.track_stock:
                        item.product.stockrecord.num_stock -= item.count
                        item.product.stockrecord.save()
                # standalone Product
                elif item.product.structure == Product.ProductTypeChoice.standalone:
                    if item.product.product_class.track_stock:
                        item.product.stockrecord.num_stock -= item.count
                        item.product.stockrecord.save()
                item.set_final_price()

            Transaction.objects.create(
                user=user,
                order=current_order,
                status=Transaction.TransactionStatusChoice.SUCCESS,
            )
            current_order.lock = False
            current_order.save()
            return BaseResponse(
                data={
                    "is_free": True,
                    "redirect_to": f"/profile/order/{current_order.slug}/",
                },
                status=status.HTTP_200_OK,
                message="در حال نهایی سازی سفارش",
            )

        if order_total_price < 1000:
            order_total_price = 1000
        transaction = Transaction.objects.create(
            user=user,
            order=current_order,
            status=Transaction.TransactionStatusChoice.WAITING,
        )
        data = {
            "MerchantID": settings.ZARINPAL_MERCHANT,
            "Amount": order_total_price,
            "Description": "نهایی کردن خرید سفارش",
            "Phone": user.phone,
            "CallbackURL": f"{settings.SITE_URL}/api/transaction/verify?order={current_order.slug}&tn={transaction.transaction_number}",
        }
        data = json.dumps(data)
        # set content length by data
        headers = {"content-type": "application/json", "content-length": str(len(data))}

        try:

            response = requests.post(
                settings.ZP_API_REQUEST, data=data, headers=headers, timeout=10
            )
            if response.status_code == 200:
                response = response.json()
                if response["Status"] == 100:
                    current_order.final_coupon_effect_price = coupon_effect_dif_price
                    current_order.final_shipping_effect_price = (
                        order_shipping_effect_price
                    )
                    current_order.payment_status = (
                        Order.PaymentStatusChoice.PENDING_PAYMENT
                    )
                    current_order.lock = False

                    current_order.save()
                    transaction.status = (
                        Transaction.TransactionStatusChoice.REDIRECT_TO_BANK
                    )
                    transaction.save()
                    return BaseResponse(
                        data={
                            "is_free": False,
                            "payment_gateway_link": settings.ZP_API_STARTPAY
                                                    + str(response["Authority"]),
                        },
                        status=status.HTTP_200_OK,
                        message="در حال انتقال به درگاه پرداخت",
                    )
                else:
                    transaction.status = Transaction.TransactionStatusChoice.FAILED
                    transaction.failed_reason = str(response["Status"])
                    transaction.save()
                    current_order.lock = False
                    current_order.save()
                    return BaseResponse(
                        data={"code": str(response["Status"])},
                        status=status.HTTP_400_BAD_REQUEST,
                        message=ResponseMessage.FAILED.value,
                    )
            transaction.status = Transaction.TransactionStatusChoice.FAILED
            transaction.failed_reason = f"status code = {response.status_code}"
            transaction.save()
            current_order.lock = False
            current_order.save()
            return response
        except requests.exceptions.Timeout:
            transaction.status = Transaction.TransactionStatusChoice.FAILED
            transaction.failed_reason = "خطای اتصال"
            transaction.save()
            current_order.lock = False
            current_order.save()
            return BaseResponse(
                data={"code": "خطای اتصال"},
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.TIME_OUT.value,
            )
        except requests.exceptions.ConnectionError:
            transaction.status = Transaction.TransactionStatusChoice.FAILED
            transaction.failed_reason = "خطای اتصال"
            transaction.save()
            current_order.lock = False
            current_order.save()
            return BaseResponse(
                data={"code": "خطای اتصال"},
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.TIME_OUT.value,
            )

        except Exception as e:
            print(e)
            transaction.status = Transaction.TransactionStatusChoice.FAILED
            transaction.failed_reason = e
            transaction.save()
            current_order.lock = False
            current_order.save()
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.TIME_OUT.value,
            )


class TransactionRePaymentRequest(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        order_slug = request.data.get("order_slug", None)

        try:
            pending_order = Order.objects.get(
                slug=order_slug,
                user=user,
                payment_status=Order.PaymentStatusChoice.PENDING_PAYMENT,
                lock=False,
                repayment_expire_at__gte=(now() - timedelta(hours=1)),
            )

            pending_order.lock = True
            pending_order.save()
        except Order.DoesNotExist:
            return BaseResponse(
                data={"redirect_to": "/"},
                status=status.HTTP_404_NOT_FOUND,
                message=ResponseMessage.FAILED.value,
            )
        if (
                pending_order.items.count() == 0
                or pending_order.shipping_rate is None
                or pending_order.address is None
        ):
            pending_order.lock = False
            pending_order.save()
            return BaseResponse(
                data={"redirect_to": "/"},
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.FAILED.value,
            )
        # Validate Address and Shipping Service
        is_valid_shipping, shipping_validate_message = (
            pending_order.is_valid_shipping_method(
                user_address=pending_order.address, shipping=pending_order.shipping_rate
            )
        )
        if not is_valid_shipping:
            pending_order.lock = False
            pending_order.save()
            return BaseResponse(
                data={"redirect_to": "/checkout/cart/"},
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.PAYMENT_NOT_VALID_SELECTED_SHIPPING.value,
            )
        order_total_price = pending_order.get_payment_price()

        if order_total_price < 1000:
            order_total_price = 1000
        transaction = Transaction.objects.create(
            user=user,
            order=pending_order,
            status=Transaction.TransactionStatusChoice.WAITING,
        )
        data = {
            "MerchantID": settings.ZARINPAL_MERCHANT,
            "Amount": order_total_price,
            "Description": "نهایی کردن خرید سفارش",
            "Phone": user.phone,
            "CallbackURL": f"{settings.SITE_URL}/api/transaction/verify?order={pending_order.slug}&tn={transaction.transaction_number}",
        }
        data = json.dumps(data)
        # set content length by data
        headers = {"content-type": "application/json", "content-length": str(len(data))}
        try:
            response = requests.post(
                settings.ZP_API_REQUEST, data=data, headers=headers, timeout=10
            )

            if response.status_code == 200:
                response = response.json()
                if response["Status"] == 100:
                    pending_order.lock = False
                    pending_order.save()
                    transaction.status = (
                        Transaction.TransactionStatusChoice.REDIRECT_TO_BANK
                    )
                    transaction.save()
                    return BaseResponse(
                        data={
                            "is_free": False,
                            "payment_gateway_link": settings.ZP_API_STARTPAY
                                                    + str(response["Authority"]),
                        },
                        status=status.HTTP_200_OK,
                        message="در حال انتقال به درگاه پرداخت",
                    )
                else:
                    transaction.status = Transaction.TransactionStatusChoice.FAILED
                    transaction.failed_reason = str(response["Status"])
                    transaction.save()
                    pending_order.lock = False
                    pending_order.save()
                    return BaseResponse(
                        data={"code": str(response["Status"])},
                        status=status.HTTP_400_BAD_REQUEST,
                        message=ResponseMessage.FAILED.value,
                    )
            transaction.status = Transaction.TransactionStatusChoice.FAILED
            transaction.failed_reason = f"status code = {response.status_code}"
            transaction.save()
            pending_order.lock = False
            pending_order.save()
            return response

        except requests.exceptions.Timeout:
            transaction.status = Transaction.TransactionStatusChoice.FAILED
            transaction.failed_reason = "خطای اتصال"
            transaction.save()
            pending_order.lock = False
            pending_order.save()
            return BaseResponse(
                data={"code": "خطای اتصال"},
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.TIME_OUT.value,
            )
        except requests.exceptions.ConnectionError:
            transaction.status = Transaction.TransactionStatusChoice.FAILED
            transaction.failed_reason = "خطای اتصال"
            transaction.save()
            pending_order.lock = False
            pending_order.save()
            return BaseResponse(
                data={"code": "خطای اتصال"},
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.TIME_OUT.value,
            )


class TransactionVerify(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        order_slug = request.GET.get("order")
        transaction_number = request.GET.get("tn")

        try:
            current_order: Order = Order.objects.prefetch_related(
                Prefetch(
                    "items",
                    queryset=OrderItem.objects.select_related(
                        "product",
                        "product__product_class",
                        "product__parent__product_class",
                        "product__stockrecord",
                    ).all(),
                )
            ).get(slug=order_slug)
            transaction = Transaction.objects.get(
                transaction_number=transaction_number, order=current_order
            )
        except Order.DoesNotExist:
            return redirect(
                f"{settings.FRONTEND_URL}/vf/tm?f={ResponseMessage.FAILED.value}"
            )
        transaction.status = Transaction.TransactionStatusChoice.RETURN_FROM_BANK
        transaction.save()

        total_price = current_order.get_payment_price()

        authority = request.GET.get("Authority", None)

        data = {
            "MerchantID": settings.ZARINPAL_MERCHANT,
            "Amount": total_price,
            "Authority": authority,
        }
        data = json.dumps(data)
        # set content length by data
        headers = {"content-type": "application/json", "content-length": str(len(data))}
        response = requests.post(settings.ZP_API_VERIFY, data=data, headers=headers)

        if response.status_code == 200:
            response = response.json()

            if response["Status"] == 100:
                current_order.final_paid_price = total_price
                current_order.final_profit_price = current_order.get_total_profit_price()
                current_order.final_total_items_final_price = current_order.get_total_items_final_price()
                current_order.final_total_items_before_discount_price = current_order.get_total_items_before_discount_price()

                current_order.payment_status = Order.PaymentStatusChoice.PAID
                current_order.save()
                current_order.ordered_at = now()
                current_order.delivery_status_modified_at = now()

                current_order.delivery_status = Order.DeliveryStatusChoice.PENDING
                current_order.repayment_expire_at = None

                for item in current_order.items.all():
                    # child Product
                    if item.product.structure == Product.ProductTypeChoice.child:
                        if item.product.parent.product_class.track_stock:
                            item.product.stockrecord.num_stock -= item.count
                            item.product.stockrecord.save()
                    # standalone Product
                    elif item.product.structure == Product.ProductTypeChoice.standalone:
                        if item.product.product_class.track_stock:
                            item.product.stockrecord.num_stock -= item.count
                            item.product.stockrecord.save()
                    item.set_final_price()
                current_order.save()
                transaction.status = Transaction.TransactionStatusChoice.SUCCESS
                transaction.ref_id = response["RefID"]
                transaction.save()
                return redirect(
                    f"{settings.FRONTEND_URL}/checkout/result/{transaction.transaction_number}/{transaction.slug}/"
                )

            else:
                errors = {
                    1: "اطلاعات ارسال شده ناقص است.",
                    -2: "IP و يا مرچنت كد پذيرنده صحيح نيست.",
                    -3: "با توجه به محدوديت هاي شاپرك امكان پرداخت با رقم درخواست شده ميسر نمي باشد.",
                    -4: "سطح تاييد پذيرنده پايين تر از سطح نقره اي است.",
                    -11: "درخواست مورد نظر يافت نشد.",
                    -12: "امكان ويرايش درخواست ميسر نمي باشد.",
                    -21: "هيچ نوع عمليات مالي براي اين تراكنش يافت نشد.",
                    -22: "تراكنش نا موفق ميباشد.",
                    -33: "رقم تراكنش با رقم پرداخت شده مطابقت ندارد.",
                    -34: "سقف تقسيم تراكنش از لحاظ تعداد يا رقم عبور نموده است.",
                    -40: "اجازه دسترسي به متد مربوطه وجود ندارد.",
                    -41: "اطلاعات ارسال شده غيرمعتبر ميباشد.",
                    -42: "مدت زمان معتبر طول عمر شناسه پرداخت بايد بين 30 دقيه تا 45 روز مي باشد.",
                    -51: "لغو توسط کاربر",
                    -54: "درخواست مورد نظر آرشيو شده است.",
                    101: "تراكنش قبلا انجام شده است.",
                }

                error_code = response["Status"]
                error_message = errors.get(
                    error_code, "خطای ناشناخته لطفا با پشتیبانی تماس بگیرید"
                )
                reason = f"Status: False,کد: {str(error_code)}, پیام: {error_message}"
                transaction.status = Transaction.TransactionStatusChoice.FAILED
                transaction.failed_reason = reason
                transaction.save()
                if response["Status"] == -51:
                    current_order.set_repayment_expire_date()
                    transaction.status = (
                        Transaction.TransactionStatusChoice.CANCEL_BY_USER
                    )
                    transaction.failed_reason = reason
                    transaction.save()
                else:
                    transaction.status = Transaction.TransactionStatusChoice.FAILED
                    transaction.failed_reason = reason
                    transaction.save()
                return redirect(
                    f"{settings.FRONTEND_URL}/checkout/result/{transaction.transaction_number}/{transaction.slug}/"
                )

        transaction.status = Transaction.TransactionStatusChoice.FAILED
        transaction.failed_reason = response
        transaction.save()
        return redirect(
            f"{settings.FRONTEND_URL}/vf/pm?f=خطای ناشناخته لطفا با پشتیبانی تماس بگیرید"
        )
