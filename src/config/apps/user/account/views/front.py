from django.db.models import Case, When, BooleanField, Subquery, OuterRef
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken

from config.api.enums import ResponseMessage
from config.api.response import BaseResponse
from config.apps.catalog.models import ProductImage, Product
from config.apps.catalog.serializers.front import ProductCardSerializer
from config.apps.messages.verification.models import (
    VerifyOTPService,
)
from config.apps.user.account.enums import UserAuthenticationCheckSectionEnum
from config.apps.user.account.models import (
    User,
    UserPasswordResetToken,
    UserFavoriteProduct,
    UserSearchHistory,
    UserRecentVisitedProduct,
)
from config.apps.user.account.serializers.front import (
    UserSerializer,
    UserLogoutSerializer,
    UserAuthenticationCheckSerializer,
    UserPasswordAuthenticationCheckSerializer,
    UserOTPAuthenticationCheckSerializer,
    UserForgotPasswordCheckSerializer,
    UserForgotPasswordOTPSerializer,
    UserForgotPasswordResetSerializer, UserEditProfileSerializer, )
from config.libs.validator.validators import validate_username, validate_password, validate_phone, validate_email


# User Get Current Detail , Required Data : Access Token
class RequestCurrentUserView(RetrieveAPIView):
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.prefetch_related("search_histories")

    def get_object(self):
        return self.get_queryset().get(pk=self.request.user.pk)

    def get(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            serializer = self.serializer_class(user)

            return BaseResponse(
                data=serializer.data,
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value,
            )
        except InvalidToken as e:
            return BaseResponse(
                status=status.HTTP_401_UNAUTHORIZED,
                message=ResponseMessage.FAILED.value,
            )


# Authentication Section -------------------------------


# User Logout  , Required Data : Refresh Token
class UserLogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserLogoutSerializer

    def post(self, request, format=None):
        serializer = UserLogoutSerializer(data=request.data)

        # Check if refresh token is provided
        if not serializer.is_valid():
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
        try:
            # Get the refresh token from the request data
            refresh_token = serializer.validated_data.get("refresh")
            # Blacklist the refresh token using Django Rest Framework SimpleJWT
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Respond with a success message
            return BaseResponse(
                status=status.HTTP_200_OK,
                message=ResponseMessage.AUTH_LOGOUT_SUCCESSFULLY.value,
            )
        except Exception as e:
            # Handle any exceptions and respond with a failure message
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


# User Authentication Check , Required Data : phone or email
# Check username and base on username type redirect to Correct Section
class UserAuthenticationCheckView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = UserAuthenticationCheckSerializer

    def post(self, request, format=None):
        serializer = UserAuthenticationCheckSerializer(data=request.data)

        # If username is not provided, return a bad request response
        if not serializer.is_valid():
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

        # Get the username from the request data and convert it to lowercase
        username = serializer.validated_data.get("username").lower()
        if not validate_username(username):
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.NOT_VALID_EMAIL_OR_PHONE.value,
            )

        # Check if the username Type is a Phone
        if User.is_phone(username):
            # Format ( add 0 at first ) the phone number if needed
            username = User.get_formatted_phone(username)

            # Check for the latest OTP service record for phone authentication
            otp_service = (
                VerifyOTPService.objects.filter(
                    type=VerifyOTPService.VerifyOTPServiceTypeChoice.PHONE,
                    to=username,
                    usage=VerifyOTPService.VerifyOTPServiceUsageChoice.AUTHENTICATE,
                )
                .order_by("-id")
                .first()
            )

            # Check if the user with the phone number exists
            user = User.objects.filter(phone=username).first()

            # If the user does not exist or does not have a usable password
            if not user or not user.has_usable_password():
                # Check for an existing OTP service record
                if otp_service and otp_service.is_expired():
                    otp_service.delete()
                    otp_service = None

                # If no OTP service record exists or it is expired, create a new one and send OTP
                if not otp_service:
                    new_otp_service = VerifyOTPService.objects.create(
                        type=VerifyOTPService.VerifyOTPServiceTypeChoice.PHONE,
                        to=username,
                        usage=VerifyOTPService.VerifyOTPServiceUsageChoice.AUTHENTICATE,
                    )

                    new_otp_service.send_otp()

                # Return success response with the section for OTP
                return BaseResponse(
                    data={"section": UserAuthenticationCheckSectionEnum.OTP.name},
                    status=status.HTTP_200_OK,
                    message=ResponseMessage.PHONE_OTP_SENT.value.format(
                        username=username
                    ),
                )

            # If OTP service record exists and is expired, delete it
            # Commented Because Celery will Handle this section

            # if otp_service and otp_service.is_expired():
            #     otp_service.delete()

            # Return success response with the section for password
            return BaseResponse(
                data={"section": UserAuthenticationCheckSectionEnum.PASSWORD.name},
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value,
            )
        # Check if the username Type is a Email
        elif User.is_email(username):
            # Check for the latest OTP service record for email authentication
            otp_service = (
                VerifyOTPService.objects.filter(
                    type=VerifyOTPService.VerifyOTPServiceTypeChoice.EMAIL,
                    to=username,
                    usage=VerifyOTPService.VerifyOTPServiceUsageChoice.AUTHENTICATE,
                )
                .order_by("-id")
                .first()
            )
            # Check if the user with the email exists
            user = User.objects.filter(email=username).first()

            if not user or not user.has_usable_password():
                # Check for an existing OTP service record
                if otp_service and otp_service.is_expired():
                    otp_service.delete()
                    otp_service = None

                # If no OTP service record exists or it is expired, create a new one and send OTP
                if not otp_service:
                    new_otp_service = VerifyOTPService.objects.create(
                        type=VerifyOTPService.VerifyOTPServiceTypeChoice.EMAIL,
                        to=username,
                        usage=VerifyOTPService.VerifyOTPServiceUsageChoice.AUTHENTICATE,
                    )
                    new_otp_service.send_otp()

                # Return success response with the section for OTP
                return BaseResponse(
                    data={"section": UserAuthenticationCheckSectionEnum.OTP.name},
                    message=ResponseMessage.EMAIL_OTP_SENT.value.format(
                        username=username
                    ),
                    status=status.HTTP_200_OK,
                )

            return BaseResponse(
                data={"section": UserAuthenticationCheckSectionEnum.PASSWORD.name},
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value,
            )
        # If the username is neither a valid phone number nor a valid email address, return a bad request response
        else:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.NOT_VALID_EMAIL_OR_PHONE.value,
            )


# User Password Login , Required Data : Username , Password
class UserPasswordAuthenticationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = UserPasswordAuthenticationCheckSerializer

    def post(self, request, format=None):
        serializer = UserPasswordAuthenticationCheckSerializer(data=request.data)

        # Check if username validation are provided
        if not serializer.is_valid():
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
            # Get username and password from request data
        username = serializer.validated_data.get("username").lower()
        password = serializer.validated_data.get("password")
        if not validate_username(username):
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

        try:
            # Format the username
            username = User.get_formatted_username(username)

            # Query the database for the user based on the username type
            user = (
                User.objects.get(phone=username)
                if User.is_phone(username)
                else User.objects.get(email=username)
            )

            # Check if the provided password matches the user's password
            if not user.check_password(password):
                return BaseResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=ResponseMessage.AUTH_WRONG_PASSWORD.value,
                )

            # User authentication successful and Logged in

            # Generate JWT token for the user
            user_tokens = user.generate_jwt_token()

            # Return success response with user token
            return BaseResponse(
                data=user_tokens,
                status=status.HTTP_200_OK,
                message=ResponseMessage.AUTH_LOGIN_SUCCESSFULLY.value,
            )

        # User does not exist in the database
        except User.DoesNotExist:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.AUTH_WRONG_PASSWORD.value,
            )


# User Otp  Login , Required Data : Username , Otp
class UserOTPAuthenticationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = UserOTPAuthenticationCheckSerializer

    def post(self, request, format=None):
        serializer = UserOTPAuthenticationCheckSerializer(data=request.data)

        # Check if username validation are provided
        if not serializer.is_valid():
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

        # Get username and OTP from request data
        username = serializer.validated_data.get("username").lower()
        otp = serializer.validated_data.get("otp").lower()

        # Check if username, OTP, and username validation are provided
        if not validate_username:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
        # Determine the type of username (email or phone) and format it
        username_type = User.get_username_type(username)
        username = User.get_formatted_username(username)
        user = None
        try:
            # Try to retrieve the user based on the formatted username
            user = User.objects.get(**{username_type.lower(): username})

        except User.DoesNotExist:
            # If user does not exist, check the OTP service
            otp_service = (
                VerifyOTPService.objects.filter(
                    type=username_type,
                    to=username,
                    code=otp,
                    usage=VerifyOTPService.VerifyOTPServiceUsageChoice.AUTHENTICATE,
                )
                .order_by("-id")
                .first()
            )
            if otp_service and not otp_service.is_expired():
                # If OTP is valid and not expired, delete the OTP service record
                otp_service.delete()
                # Create a new user based on the username type
                user = User.objects.create_user(
                    **{username_type.lower(): username}, password=None
                )
                # User created successfully and logged in
                # Continue
            else:
                # Invalid or expired OTP
                return BaseResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=ResponseMessage.AUTH_WRONG_OTP.value,
                )

        else:
            # User exists, check the OTP service
            otp_service = (
                VerifyOTPService.objects.filter(
                    type=username_type,
                    to=username,
                    code=otp,
                    usage=VerifyOTPService.VerifyOTPServiceUsageChoice.AUTHENTICATE,
                )
                .order_by("-id")
                .first()
            )
            if otp_service and not otp_service.is_expired():
                # If OTP is valid and not expired, delete the OTP service record
                otp_service.delete()

                # User logged in successfully
            else:
                # Invalid or expired OTP
                if otp_service and otp_service.is_expired():
                    otp_service.delete()
                return BaseResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=ResponseMessage.AUTH_WRONG_OTP.value,
                )

        # Generate JWT token for the user
        user_tokens = user.generate_jwt_token()

        return BaseResponse(
            data=user_tokens,
            status=status.HTTP_200_OK,
            message=ResponseMessage.AUTH_LOGIN_SUCCESSFULLY.value,
        )


# Forgot Password Section -------------------------------


# User ForgotPassword Check  , Required Data : Username (email or phone)
class UserForgotPasswordCheckView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = UserForgotPasswordCheckSerializer

    def post(self, request, format=None):
        serializer = UserForgotPasswordCheckSerializer(data=request.data)

        if not serializer.is_valid():
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

        # Get username from request data
        username = serializer.validated_data.get("username").lower()

        # Check if username validation are provided
        if not validate_username(username):
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

        # Determine OTP type, response message, and format the username
        otp_type = (
            VerifyOTPService.VerifyOTPServiceTypeChoice.PHONE
            if User.is_phone(username)
            else VerifyOTPService.VerifyOTPServiceTypeChoice.EMAIL
        )
        message = (
            ResponseMessage.PHONE_OTP_SENT.value
            if User.is_phone(username)
            else ResponseMessage.EMAIL_OTP_SENT.value
        )
        username = User.get_formatted_username(username)
        try:
            # Try to retrieve the user based on the formatted username
            user = User.objects.get(
                **{User.get_username_type(username).lower(): username}
            )

        except User.DoesNotExist:
            # User not found for password reset
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.RESET_PASSWORD_USER_NOT_FOUND.value,
            )

            # Get or create an OTP service record for password reset
        otp_service, _ = VerifyOTPService.objects.get_or_create(
            type=otp_type,
            to=username,
            usage=VerifyOTPService.VerifyOTPServiceUsageChoice.RESET_PASSWORD,
        )

        if otp_service.is_expired():
            # If OTP is expired, delete and set to None
            otp_service.delete()
            otp_service = None

        if not otp_service:
            # If no OTP service record, create and send OTP
            otp_service = VerifyOTPService.objects.create(
                type=otp_type,
                to=username,
                usage=VerifyOTPService.VerifyOTPServiceUsageChoice.RESET_PASSWORD,
            )
            otp_service.send_otp()

        # Return success response with the appropriate message
        return BaseResponse(
            status=status.HTTP_200_OK, message=message.format(username=username)
        )


# User ForgotPassword Validate OTP  , Required Data : Username (email or phone) , OTP code
class UserForgotPasswordOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = UserForgotPasswordOTPSerializer

    def post(self, request, format=None):
        serializer = UserForgotPasswordOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

        # Get username , otp from request data
        username = serializer.validated_data.get("username").lower()
        otp = serializer.validated_data.get("otp")

        if not validate_username(username):
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

        # Determine username type and format the username
        username_type = User.get_username_type(username)
        username = User.get_formatted_username(username)
        try:
            # Try to retrieve the user based on the formatted username
            user = User.objects.get(**{username_type.lower(): username})
            # Check the OTP service record for password reset
            otp_service = (
                VerifyOTPService.objects.filter(
                    type=username_type,
                    to=username,
                    code=otp,
                    usage=VerifyOTPService.VerifyOTPServiceUsageChoice.RESET_PASSWORD,
                )
                .order_by("-id")
                .first()
            )
            if not otp_service or otp_service.is_expired():
                # Invalid or expired OTP

                return BaseResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=ResponseMessage.AUTH_WRONG_OTP.value,
                )
            # Delete the OTP service record and return success with the forgot password token

            otp_service.delete()
            return BaseResponse(
                data={"token": user.generate_password_reset_token()},
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            # User not found for password reset

            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.RESET_PASSWORD_USER_NOT_FOUND.value,
            )


# User ForgotPassword ResetPassword Final Stage  ,
# Required Data : Username (email or phone) , Token, new password, confirm new password
class UserForgotPasswordResetView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = UserForgotPasswordResetSerializer

    def post(self, request, format=None):
        serializer = UserForgotPasswordResetSerializer(data=request.data)

        if not serializer.is_valid():
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

        # Get and validate request data
        username = serializer.validated_data.get("username").lower()
        token = serializer.validated_data.get("token")
        token = token.strip('"')

        password = serializer.validated_data.get("password")
        confirm_password = serializer.validated_data.get("confirm_password")

        if not validate_username(username):
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
        # Validate password
        is_valid, message = validate_password(password)
        if not is_valid:
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST, message=message)
        if password != confirm_password:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.PASSWORD_CONFIRM_MISMATCH.value,
            )
        # Determine username type and format the username
        username = User.get_formatted_username(username)

        try:
            # Try to retrieve the user based on the formatted username

            user = User.objects.get(
                **{User.get_username_type(username).lower(): username}
            )

            # Set the new password, revoke all tokens, and save the user

            token_object = UserPasswordResetToken.objects.get(
                user=user, token=token, expire_at__gt=timezone.now()
            )
            # Check and delete the password reset token
            token_object.delete()
            user.set_password(password)
            user.revoke_all_tokens()
            user.save()
            return BaseResponse(
                status=status.HTTP_200_OK,
                message=ResponseMessage.RESET_PASSWORD_SUCCESSFULLY.value,
            )
        except User.DoesNotExist:
            # User not found
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
        except UserPasswordResetToken.DoesNotExist:
            # Password reset token not found or expired

            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
        except Exception as e:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class UserFavoriteProductView(APIView):
    def get(self, request, *args, **kwargs):

        try:
            user = request.user
            user_favorites = UserFavoriteProduct.objects.only('product_id').select_related('product').filter(user=user)
            user_favorites_products_id = [item.product_id for item in user_favorites]
            products = (Product.objects.only(
                "id",
                "title_ir",
                "title_en",
                "slug",
                "short_slug",
                "structure",
                "brand__title_en",
                "brand__title_ir",
                "brand__slug",
                "product_class__track_stock",
            )
            .select_related("brand", "stockrecord", "product_class")
            .filter(
                id__in=user_favorites_products_id,
                is_public=True,
            )
            .annotate(
                is_available=Case(
                    When(
                        product_class__track_stock=True,
                        then=Case(
                            When(stockrecord__num_stock__gt=0, then=True),
                            default=False,
                            output_field=BooleanField(),
                        ),
                    ),
                    default=True,
                    output_field=BooleanField(),
                )
            )
            .order_by("-is_available")
            .annotate(
                primary_image_file=Subquery(
                    ProductImage.objects.select_related("image")
                    .filter(product=OuterRef("pk"))
                    .values("image__file")[:1]
                )
            ))

            data = ProductCardSerializer(products, many=True).data
            return BaseResponse(
                data=data,
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value
            )

        except Exception as e:
            print(e)
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

    def post(self, request):

        try:
            user = request.user
            product_ids = request.data.get("product_ids", [])
            if not product_ids:
                return BaseResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=ResponseMessage.FAILED.value,
                )

            user_favorites = (
                UserFavoriteProduct.objects.select_related("product")
                .only("id", "user", "product_id")
                .filter(user=user)
            )
            user_favorite_product_ids = list(
                [product.product.id for product in user_favorites]
            )
            if len(product_ids) == 1:
                if product_ids[0] in user_favorite_product_ids:
                    user_favorites.get(product_id=product_ids[0]).delete()
                    return BaseResponse(
                        status=status.HTTP_204_NO_CONTENT,
                        message=ResponseMessage.PRODUCT_REMOVED_FROM_FAVORITE_SUCCESSFULLY.value,
                    )

                # check if user already have 20 favorites, remove the oldest one
                if len(user_favorite_product_ids) >= 20:
                    user_favorites.filter(user=user).order_by(
                        "created_at"
                    ).first().delete()

                UserFavoriteProduct.objects.create(user=user, product_id=product_ids[0])

                return BaseResponse(
                    status=status.HTTP_201_CREATED,
                    message=ResponseMessage.PRODUCT_ADDED_TO_FAVORITE_SUCCESSFULLY.value,
                )
            else:
                for product_id in product_ids:
                    if product_id not in user_favorite_product_ids:
                        UserFavoriteProduct.objects.get_or_create(
                            user=user, product_id=product_id
                        )
                return BaseResponse(
                    status=status.HTTP_201_CREATED,
                    message=ResponseMessage.PRODUCT_ADDED_TO_FAVORITE_SUCCESSFULLY.value,
                )
        except Exception as e:
            print(e)
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

    def delete(self, request):
        try:
            user = request.user
            product_id = request.data.get("product_id")
            UserFavoriteProduct.objects.get(user=user, product_id=product_id).delete()
            return BaseResponse(
                status=status.HTTP_204_NO_CONTENT,
                message=ResponseMessage.PRODUCT_REMOVED_FROM_FAVORITE_SUCCESSFULLY.value,
            )
        except UserFavoriteProduct.DoesNotExist:
            return BaseResponse(
                status=status.HTTP_404_NOT_FOUND, message=ResponseMessage.FAILED.value
            )
        except Exception as e:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class UserFavoriteProductClearView(APIView):

    def delete(self, request):
        try:
            user = request.user
            UserFavoriteProduct.objects.filter(user=user).delete()
            return BaseResponse(
                status=status.HTTP_204_NO_CONTENT,
                message=ResponseMessage.PRODUCTS_CLEAR_FROM_FAVORITE_SUCCESSFULLY.value,
            )
        except Exception as e:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class UserSearchHistoryView(APIView):
    def post(self, request):
        search = request.data.get("search")
        if not search:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

        try:
            user = request.user
            UserSearchHistory.objects.get_or_create(user=user, search=search)
            return BaseResponse(
                status=status.HTTP_204_NO_CONTENT, message=ResponseMessage.SUCCESS.value
            )
        except Exception as e:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

    def delete(self, request):
        # NOTE : Clear User All Search History
        try:
            user = request.user

            UserSearchHistory.objects.filter(user=user).delete()
            return BaseResponse(
                status=status.HTTP_204_NO_CONTENT, message=ResponseMessage.SUCCESS.value
            )
        except Exception as e:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class UserRecentVisitedProductView(APIView):
    def get(self, request, *args, **kwargs):

        try:
            user = request.user
            user_recent = UserRecentVisitedProduct.objects.only('product_id').select_related('product').filter(
                user=user)
            user_recent_products_id = [item.product_id for item in user_recent]
            products = (Product.objects.only(
                "id",
                "title_ir",
                "title_en",
                "slug",
                "short_slug",
                "structure",
                "brand__title_en",
                "brand__title_ir",
                "brand__slug",
                "product_class__track_stock",
            )
            .select_related("brand", "stockrecord", "product_class")
            .filter(
                id__in=user_recent_products_id,
                is_public=True,
            )
            .annotate(
                is_available=Case(
                    When(
                        product_class__track_stock=True,
                        then=Case(
                            When(stockrecord__num_stock__gt=0, then=True),
                            default=False,
                            output_field=BooleanField(),
                        ),
                    ),
                    default=True,
                    output_field=BooleanField(),
                )
            )
            .order_by("-is_available")
            .annotate(
                primary_image_file=Subquery(
                    ProductImage.objects.select_related("image")
                    .filter(product=OuterRef("pk"))
                    .values("image__file")[:1]
                )
            ))

            data = ProductCardSerializer(products, many=True).data
            return BaseResponse(
                data=data,
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value
            )

        except Exception as e:
            print(e)
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

    def post(self, request):
        product_ids = request.data.get("product_ids", [])
        if not product_ids:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

        try:
            user = request.user
            for id in product_ids:
                UserRecentVisitedProduct.objects.get_or_create(user=user, product_id=id)
            return BaseResponse(
                status=status.HTTP_204_NO_CONTENT, message=ResponseMessage.SUCCESS.value
            )
        except Exception as e:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

    def delete(self, request):
        try:
            user = request.user
            product_id = request.data.get("product_id")
            UserRecentVisitedProduct.objects.get(user=user, product_id=product_id).delete()
            return BaseResponse(
                status=status.HTTP_204_NO_CONTENT,
                message=ResponseMessage.SUCCESS.value,
            )
        except UserFavoriteProduct.DoesNotExist:
            return BaseResponse(
                status=status.HTTP_404_NOT_FOUND, message=ResponseMessage.FAILED.value
            )
        except Exception as e:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class UserRecentVisitedProductClearView(APIView):

    def delete(self, request):
        try:
            user = request.user
            UserRecentVisitedProduct.objects.filter(user=user).delete()
            return BaseResponse(
                status=status.HTTP_204_NO_CONTENT,
                message=ResponseMessage.PRODUCTS_CLEAR_FROM_RECENT_SUCCESSFULLY.value,
            )
        except Exception as e:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


# Profile


class UserUpdateDetailView(UpdateAPIView):
    serializer_class = UserEditProfileSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        try:
            user = self.request.user
            serializer = self.serializer_class(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return BaseResponse(status=status.HTTP_204_NO_CONTENT,
                                message=ResponseMessage.SUCCESS.value)
        except Exception as e:
            print(e)
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)


class UserEditPhoneRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        phone = request.data.get('phone', None).lower()
        otp_usage = request.data.get('otp_usage', None)

        if not phone or not otp_usage:
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)

        if validate_phone(phone):
            phone = User.get_formatted_phone(phone)

            if User.objects.filter(phone=phone).exists():
                return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                    message=ResponseMessage.USER_PANEL_PHONE_ALREADY_EXIST.value)
            # Check for the latest OTP service record for phone authentication
            otp_service = (
                VerifyOTPService.objects.filter(
                    type=VerifyOTPService.VerifyOTPServiceTypeChoice.PHONE,
                    to=phone,
                    usage=otp_usage,
                )
                .order_by("-id")
                .first()
            )
            if otp_service:
                if otp_service.is_expired():
                    otp_service.delete()
                    new_otp_service = VerifyOTPService.objects.create(
                        type=VerifyOTPService.VerifyOTPServiceTypeChoice.PHONE,
                        to=phone,
                        usage=otp_usage)
                    new_otp_service.send_otp()

                    return BaseResponse(status=status.HTTP_200_OK,
                                        message=ResponseMessage.PHONE_OTP_SENT.value.format(username=phone))
                else:
                    return BaseResponse(status=status.HTTP_200_OK,
                                        message=ResponseMessage.PHONE_OTP_SENT.value.format(username=phone))
            else:
                new_otp_service = VerifyOTPService.objects.create(
                    type=VerifyOTPService.VerifyOTPServiceTypeChoice.PHONE, to=phone, usage=otp_usage)

                new_otp_service.send_otp()
                return BaseResponse(status=status.HTTP_200_OK,
                                    message=ResponseMessage.PHONE_OTP_SENT.value.format(username=phone))
        else:
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.NOT_VALID_PHONE.value)


class UserEditPhoneConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        phone = request.data.get('phone', None).lower()
        otp = request.data.get('otp', None)
        user = self.request.user

        phone = User.get_formatted_phone(phone)

        if not phone or not otp or (phone == user.phone):
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)

        otp_service = VerifyOTPService.objects.filter(type=VerifyOTPService.VerifyOTPServiceTypeChoice.PHONE, to=phone,
                                                      code=otp,
                                                      usage=VerifyOTPService.VerifyOTPServiceUsageChoice.VERIFY).order_by(
            '-id').first()

        if not otp_service or otp_service.is_expired():
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.AUTH_WRONG_OTP.value)

        otp_service.delete()
        user.phone = phone
        user.revoke_all_tokens()
        user.save()

        # Generate JWT token for the user
        refresh_token = RefreshToken.for_user(user)
        access_token = refresh_token.access_token

        user_token = {
            'access': str(access_token),
            'refresh': str(refresh_token),
        }
        return BaseResponse(data=user_token, status=status.HTTP_200_OK,
                            message=ResponseMessage.SUCCESS.value)


class UserEditEmailRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        email = request.data.get('email', None).lower()
        otp_usage = request.data.get('otp_usage', None)
        if not email or not otp_usage:
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)

        if validate_email(email):
            if User.objects.filter(email=email).exists():
                return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                    message=ResponseMessage.USER_PANEL_EMAIL_ALREADY_EXIST.value)
            # Check for the latest OTP service record for phone authentication
            otp_service = (
                VerifyOTPService.objects.filter(
                    type=VerifyOTPService.VerifyOTPServiceTypeChoice.EMAIL,
                    to=email,
                    usage=otp_usage,
                )
                .order_by("-id")
                .first()
            )
            if otp_service:
                if otp_service.is_expired():
                    otp_service.delete()
                    new_otp_service = VerifyOTPService.objects.create(
                        type=VerifyOTPService.VerifyOTPServiceTypeChoice.EMAIL, to=email, usage=otp_usage)
                    new_otp_service.send_otp()

                    return BaseResponse(status=status.HTTP_200_OK,
                                        message=ResponseMessage.EMAIL_OTP_SENT.value.format(username=email))
                else:
                    return BaseResponse(status=status.HTTP_200_OK,
                                        message=ResponseMessage.EMAIL_OTP_SENT.value.format(username=email))
            else:
                new_otp_service = VerifyOTPService.objects.create(
                    type=VerifyOTPService.VerifyOTPServiceTypeChoice.EMAIL, to=email, usage=otp_usage)

                new_otp_service.send_otp()
                return BaseResponse(status=status.HTTP_200_OK,
                                    message=ResponseMessage.EMAIL_OTP_SENT.value.format(username=email))
        else:
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.NOT_VALID_EMAIL.value)


class UserEditEmailConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        email = request.data.get('email', None).lower()
        otp = request.data.get('otp', None)
        user = self.request.user

        if not email or not otp or (email == user.email):
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)

        otp_service = VerifyOTPService.objects.filter(type=VerifyOTPService.VerifyOTPServiceTypeChoice.EMAIL, to=email,
                                                      code=otp,
                                                      usage=VerifyOTPService.VerifyOTPServiceUsageChoice.VERIFY).order_by(
            '-id').first()

        if not otp_service or otp_service.is_expired():
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.AUTH_WRONG_OTP.value)

        otp_service.delete()
        user.email = email
        user.revoke_all_tokens()
        user.save()

        # Generate JWT token for the user
        refresh_token = RefreshToken.for_user(user)
        access_token = refresh_token.access_token

        user_token = {
            'access': str(access_token),
            'refresh': str(refresh_token),
        }
        return BaseResponse(data=user_token, status=status.HTTP_200_OK,
                            message=ResponseMessage.SUCCESS.value)


class UserEditPassword(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, format=None):
        current_password = request.data.get('current_password')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        user = self.request.user

        if user.has_usable_password() and not user.check_password(current_password):
            return BaseResponse(data={'error_input_name': 'current_password'}, status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.USER_PANEL_CURRENT_PASSWORD_WRONG.value)
        is_valid, message = validate_password(password)
        if not is_valid:
            return BaseResponse(data={'error_input_name': 'password'}, status=status.HTTP_400_BAD_REQUEST,
                                message=message)
        if password != confirm_password:
            return BaseResponse(data={'error_input_name': 'confirm_password'}, status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.PASSWORD_CONFIRM_MISMATCH.value)

        user.set_password(password)
        user.revoke_all_tokens()
        user.save()

        # Generate JWT token for the user
        refresh_token = RefreshToken.for_user(user)
        access_token = refresh_token.access_token

        user_token = {
            'access': str(access_token),
            'refresh': str(refresh_token),
        }
        return BaseResponse(data=user_token, status=status.HTTP_200_OK,
                            message=ResponseMessage.RESET_PASSWORD_SUCCESSFULLY.value)
