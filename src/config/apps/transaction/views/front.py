import json

import requests
from django.conf import settings
from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.api.enums import ResponseMessage
from config.api.response import BaseResponse
from config.apps.catalog.models import Product
from config.apps.order.models import Order, ShippingRate, OrderAddress, Coupon
from config.apps.transaction.models import Transaction
from config.apps.user.address.models import UserAddresses


class OrderTransactionRequest(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        try:
            current_order: Order = Order.objects.prefetch_related('items').get(
                user=user, payment_status=Order.PaymentStatusChoice.OPEN_ORDER, lock=False
            )
            current_order.lock = True
            current_order.save()

        except Order.DoesNotExist:
            return BaseResponse(data={"redirect_to": "/checkout/cart/"}, status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)
        if current_order.items.count() == 0:
            current_order.lock = False
            current_order.save()
            return BaseResponse(data={"redirect_to": "/checkout/cart/"}, status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)
        address = request.data.get('address', None)
        shipping = request.data.get('shipping', None)

        if not address or not shipping:
            current_order.lock = False
            current_order.save()
            return BaseResponse(data={"redirect_to": "/checkout/shipping/"}, status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)

        try:
            selected_shipping = ShippingRate.objects.get(id=shipping['id'], is_public=True)
            selected_address = UserAddresses.objects.get(user=user, id=address['id'])
        except (ShippingRate.DoesNotExist, UserAddresses.DoesNotExist):
            current_order.lock = False
            current_order.save()
            return BaseResponse(data={"redirect_to": "/checkout/shipping/"}, status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.PAYMENT_NOT_VALID_SELECTED_SHIPPING_OR_ADDRESS.value)

        # Validate Address and Shipping Service
        is_valid_shipping, shipping_validate_message = current_order.is_valid_shipping_method(
            user_address=selected_address,
            shipping=selected_shipping)

        if not is_valid_shipping:
            current_order.lock = False
            current_order.save()
            return BaseResponse(data={"redirect_to": "/checkout/shipping/"}, status=status.HTTP_400_BAD_REQUEST,
                                message=shipping_validate_message)

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
            current_order.address.receiver_unit = (
                selected_address.receiver_unit
            )
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

        current_order.shipping = selected_shipping
        current_order.save()
        # Address and Shipping are Valid.
        coupon_code = request.data.get('coupon_code', None)
        order_total_price = order_total_price_before_coupon = current_order.get_total_price()
        order_shipping_effect_price = current_order.shipping.calculate_price(
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
                status=Transaction.TransactionStatusChoice.SUCCESS
            )
            current_order.lock = False
            current_order.save()
            return BaseResponse(
                data={
                    "is_free": True,
                    "redirect_to": f"{settings.FRONTEND_URL}/panel/orders/{current_order.slug}/",
                },
                status=status.HTTP_200_OK,
                message="در حال نهایی سازی سفارش",
            )
        if order_total_price < 1000:
            order_total_price = 1000
        data = {
            "MerchantID": settings.ZARINPAL_MERCHANT,
            "Amount": order_total_price,
            "Description": "نهایی کردن خرید سفارش",
            "Phone": user.phone,
            "CallbackURL": f"{settings.BACKEND_URL}/api/transaction/verify?order={current_order.slug}",
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
                    current_order.coupon_effect_price = coupon_effect_dif_price
                    current_order.shipping_effect_price = coupon_effect_dif_price
                    current_order.payment_status = Order.PaymentStatusChoice.PENDING_PAYMENT
                    current_order.set_repayment_expire_date()
                    current_order.lock = False

                    current_order.save()
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
                    current_order.lock = False
                    current_order.save()
                    return BaseResponse(
                        data={"code": str(response["Status"])},
                        status=status.HTTP_400_BAD_REQUEST,
                        message=ResponseMessage.FAILED.value,
                    )
            current_order.lock_for_payment = False
            current_order.save()
            return response
        except requests.exceptions.Timeout:
            current_order.lock = False
            current_order.save()
            return BaseResponse(
                data={"code": "خطای اتصال"},
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.TIME_OUT.value,
            )
        except requests.exceptions.ConnectionError:
            current_order.lock = False
            current_order.save()
            return BaseResponse(
                data={"code": "خطای اتصال"},
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.TIME_OUT.value,
            )
