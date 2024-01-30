from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from config.api.enums import ResponseMessage
from config.api.response import BaseResponse
from config.apps.content.models import Banner
from config.apps.content.serializers.front import HomeDataSerializer, BannerSerializer


class GetHomeDataView(APIView):
    serializer_class = HomeDataSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            # TODO Cache
            # Check if data is in cache
            # cached_banners = cache.get("cached_banners")
            # if cached_banners:
            #     return BaseResponse(
            #         {
            #             "banners": cached_banners,
            #         },
            #         status=status.HTTP_200_OK,
            #         message=ResponseMessage.SUCCESS.value,
            #     )

            banners = Banner.objects.all().select_related('image')

            # Serialize the data
            response_data = {
                "banners": BannerSerializer(banners, many=True).data,
                "products_nike": [],
                "products_salomon": [],
                "products_adidas": [],
                "products_newbalance": [],
            }

            # Set data in cache
            # cache.set(
            #     "cached_banners", response_data["banners"], timeout=None
            # )  # No expiration for banners

            return BaseResponse(
                response_data,
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value,
            )

        except Exception as e:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
