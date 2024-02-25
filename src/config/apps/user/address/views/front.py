from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.api.enums import ResponseMessage
from config.api.response import BaseResponse
from config.apps.user.address.models import UserAddresses
from config.apps.user.address.serializers.front import UserAddressesSerializer


class UserAddressAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_addresses = UserAddresses.objects.filter(user=request.user)
        serializer = UserAddressesSerializer(user_addresses, many=True)
        return BaseResponse(
            data=serializer.data,
            status=status.HTTP_200_OK,
            message=ResponseMessage.SUCCESS.value,
        )

    def post(self, request):
        serializer = UserAddressesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return BaseResponse(
                data=serializer.data,
                status=status.HTTP_201_CREATED,
                message=ResponseMessage.USER_PANEL_ADDRESS_ADDED_SUCCESSFULLY.value,
            )
        return BaseResponse(
            status=status.HTTP_400_BAD_REQUEST,
            message=serializer.errors,
        )

    def put(self, request):
        try:
            serializer = UserAddressesSerializer(data=request.data)
            if serializer.is_valid():
                address = UserAddresses.objects.get(
                    id=request.data.get("id"), user=request.user
                )
                serializer.update(address, serializer.validated_data)
                return BaseResponse(
                    status=status.HTTP_204_NO_CONTENT,
                    message=ResponseMessage.USER_PANEL_ADDRESS_EDITED_SUCCESSFULLY.value,
                )
            return BaseResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserAddresses.DoesNotExist:
            return BaseResponse(
                status=status.HTTP_404_NOT_FOUND,
                message=ResponseMessage.USER_PANEL_ADDRESS_NOT_FOUND.value,
            )

    def delete(self, request):
        try:
            address_id = self.request.data.get("id", None)
            address = UserAddresses.objects.get(id=address_id, user=request.user)
            address.delete()
            return BaseResponse(
                status=status.HTTP_204_NO_CONTENT,
                message=ResponseMessage.USER_PANEL_ADDRESS_REMOVED_SUCCESSFULLY.value,
            )
        except UserAddresses.DoesNotExist:
            return BaseResponse(
                status=status.HTTP_404_NOT_FOUND,
                message=ResponseMessage.USER_PANEL_ADDRESS_NOT_FOUND.value,
            )
