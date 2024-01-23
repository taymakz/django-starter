from django.utils import timezone
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken

from config.api.enums import ResponseMessage
from config.api.response import BaseResponse
from config.apps.messages.verification.models import VerifyOTPService, VerificationMessageUsageOptions, \
    VerificationMessageTypeOptions
from config.apps.user.account.enums import UserAuthenticationCheckSectionEnum
from config.apps.user.account.models import User, UserPasswordResetToken
from config.apps.user.account.serializers.front import UserSerializer, UserLogoutSerializer, \
    UserAuthenticationCheckSerializer, UserPasswordAuthenticationCheckSerializer, UserOTPAuthenticationCheckSerializer, \
    UserForgotPasswordCheckSerializer, UserForgotPasswordOTPSerializer, UserForgotPasswordResetSerializer
from config.libs.validator.validators import validate_username, validate_password


# User Get Current Detail , Required Data : Access Token
class RequestCurrentUserView(RetrieveAPIView):
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            serializer = self.serializer_class(user)

            return BaseResponse(data=serializer.data, status=status.HTTP_200_OK,
                                message=ResponseMessage.SUCCESS.value)
        except InvalidToken as e:
            return BaseResponse(status=status.HTTP_401_UNAUTHORIZED,
                                message=ResponseMessage.FAILED.value)


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
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)
        try:
            # Get the refresh token from the request data
            refresh_token = serializer.validated_data.get('refresh')
            # Blacklist the refresh token using Django Rest Framework SimpleJWT
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Respond with a success message
            return BaseResponse(status=status.HTTP_200_OK,
                                message=ResponseMessage.AUTH_LOGOUT_SUCCESSFULLY.value)
        except Exception as e:
            # Handle any exceptions and respond with a failure message
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)


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
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)

        # Get the username from the request data and convert it to lowercase
        username = serializer.validated_data.get('username').lower()
        if not validate_username(username):
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.NOT_VALID_EMAIL_OR_PHONE.value)

        # Check if the username Type is a Phone
        if User.is_phone(username):
            # Format ( add 0 at first ) the phone number if needed
            username = User.get_formatted_phone(username)

            # Check for the latest OTP service record for phone authentication
            otp_service = (
                VerifyOTPService.objects.filter(
                    type=VerificationMessageTypeOptions.PHONE.name,
                    to=username,
                    usage=VerificationMessageUsageOptions.AUTHENTICATE.name
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
                        type=VerificationMessageTypeOptions.PHONE.name,
                        to=username,
                        usage=VerificationMessageUsageOptions.AUTHENTICATE.name
                    )

                    new_otp_service.send_otp()

                # Return success response with the section for OTP
                return BaseResponse(
                    data={'section': UserAuthenticationCheckSectionEnum.OTP.name},
                    status=status.HTTP_200_OK,
                    message=ResponseMessage.PHONE_OTP_SENT.value.format(username=username)
                )

            # If OTP service record exists and is expired, delete it
            # Commented Because Celery will Handle this section

            # if otp_service and otp_service.is_expired():
            #     otp_service.delete()

            # Return success response with the section for password
            return BaseResponse(
                data={'section': UserAuthenticationCheckSectionEnum.PASSWORD.name},
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value
            )
        # Check if the username Type is a Email
        elif User.is_email(username):
            # Check for the latest OTP service record for email authentication
            otp_service = (
                VerifyOTPService.objects.filter(
                    type=VerificationMessageTypeOptions.EMAIL.name,
                    to=username,
                    usage=VerificationMessageUsageOptions.AUTHENTICATE.name
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
                        type=VerificationMessageTypeOptions.EMAIL.name,
                        to=username,
                        usage=VerificationMessageUsageOptions.AUTHENTICATE.name
                    )
                    new_otp_service.send_otp()

                # Return success response with the section for OTP
                return BaseResponse(
                    data={'section': UserAuthenticationCheckSectionEnum.OTP.name},
                    message=ResponseMessage.EMAIL_OTP_SENT.value.format(
                        username=username
                    ),
                    status=status.HTTP_200_OK,
                )
            # If OTP service record exists and is expired, delete it
            # TODO : Commented Because Celery will Handle this section

            # if otp_service and otp_service.is_expired():
            #     otp_service.delete()

            return BaseResponse(
                data={'section': UserAuthenticationCheckSectionEnum.PASSWORD.name},
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value
            )
        # If the username is neither a valid phone number nor a valid email address, return a bad request response
        else:
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.NOT_VALID_EMAIL_OR_PHONE.value)


# User Password Login , Required Data : Username , Password
class UserPasswordAuthenticationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = UserPasswordAuthenticationCheckSerializer

    def post(self, request, format=None):

        serializer = UserPasswordAuthenticationCheckSerializer(data=request.data)

        # Check if username validation are provided
        if not serializer.is_valid():
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)
            # Get username and password from request data
        username = serializer.validated_data.get('username').lower()
        password = serializer.validated_data.get('password')
        if not validate_username(username):
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)

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
                return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                    message=ResponseMessage.AUTH_WRONG_PASSWORD.value)

            # User authentication successful and Logged in

            # Generate JWT token for the user
            user_tokens = user.generate_jwt_token()

            # Return success response with user token
            return BaseResponse(data=user_tokens, status=status.HTTP_200_OK,
                                message=ResponseMessage.AUTH_LOGIN_SUCCESSFULLY.value)

        # User does not exist in the database
        except User.DoesNotExist:
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.AUTH_WRONG_PASSWORD.value)


# User Otp  Login , Required Data : Username , Otp
class UserOTPAuthenticationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = UserOTPAuthenticationCheckSerializer

    def post(self, request, format=None):

        serializer = UserOTPAuthenticationCheckSerializer(data=request.data)

        # Check if username validation are provided
        if not serializer.is_valid():
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)

        # Get username and OTP from request data
        username = serializer.validated_data.get('username').lower()
        otp = serializer.validated_data.get('otp').lower()

        # Check if username, OTP, and username validation are provided
        if not validate_username:
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)
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
                    usage=VerificationMessageUsageOptions.AUTHENTICATE.name
                )
                .order_by("-id")
                .first()
            )
            if otp_service and not otp_service.is_expired():
                # If OTP is valid and not expired, delete the OTP service record
                otp_service.delete()
                # Create a new user based on the username type
                user = User.objects.create_user(**{username_type.lower(): username}, password=None)
                # User created successfully and logged in
                # Continue
            else:
                # Invalid or expired OTP
                return BaseResponse(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=ResponseMessage.AUTH_WRONG_OTP.value
                )

        else:
            # User exists, check the OTP service
            otp_service = (
                VerifyOTPService.objects.filter(
                    type=username_type,
                    to=username,
                    code=otp,
                    usage=VerificationMessageUsageOptions.AUTHENTICATE.name
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
                    message=ResponseMessage.AUTH_WRONG_OTP.value
                )

        # Generate JWT token for the user
        user_tokens = user.generate_jwt_token()

        return BaseResponse(data=user_tokens, status=status.HTTP_200_OK,
                            message=ResponseMessage.AUTH_LOGIN_SUCCESSFULLY.value)


# Forgot Password Section -------------------------------

# User ForgotPassword Check  , Required Data : Username (email or phone)
class UserForgotPasswordCheckView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = UserForgotPasswordCheckSerializer

    def post(self, request, format=None):
        serializer = UserForgotPasswordCheckSerializer(data=request.data)

        if not serializer.is_valid():
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)

        # Get username from request data
        username = serializer.validated_data.get('username').lower()

        # Check if username validation are provided
        if not validate_username(username):
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)

        # Determine OTP type, response message, and format the username
        otp_type = VerificationMessageTypeOptions.PHONE.name if User.is_phone(
            username) else VerificationMessageTypeOptions.EMAIL.name
        message = ResponseMessage.PHONE_OTP_SENT.value if User.is_phone(
            username) else ResponseMessage.EMAIL_OTP_SENT.value
        username = User.get_formatted_username(username)
        try:
            # Try to retrieve the user based on the formatted username
            user = User.objects.get(**{User.get_username_type(username).lower(): username})

        except User.DoesNotExist:
            # User not found for password reset
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.RESET_PASSWORD_USER_NOT_FOUND.value
            )

            # Get or create an OTP service record for password reset
        otp_service, _ = VerifyOTPService.objects.get_or_create(
            type=otp_type,
            to=username,
            usage=VerificationMessageUsageOptions.RESET_PASSWORD.name
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
                usage=VerificationMessageUsageOptions.RESET_PASSWORD.name
            )
            otp_service.send_otp()

        # Return success response with the appropriate message
        return BaseResponse(status=status.HTTP_200_OK,
                            message=message.format(username=username))


# User ForgotPassword Validate OTP  , Required Data : Username (email or phone) , OTP code
class UserForgotPasswordOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = UserForgotPasswordOTPSerializer

    def post(self, request, format=None):

        serializer = UserForgotPasswordOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)

        # Get username , otp from request data
        username = serializer.validated_data.get('username').lower()
        otp = serializer.validated_data.get('otp')

        if not validate_username(username):
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)

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
                    usage=VerificationMessageUsageOptions.RESET_PASSWORD.name
                )
                .order_by("-id")
                .first()
            )
            if not otp_service or otp_service.is_expired():
                # Invalid or expired OTP

                return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                    message=ResponseMessage.AUTH_WRONG_OTP.value)
            # Delete the OTP service record and return success with the forgot password token

            otp_service.delete()
            return BaseResponse(data={'token': user.generate_password_reset_token()}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            # User not found for password reset

            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.RESET_PASSWORD_USER_NOT_FOUND.value)


# User ForgotPassword ResetPassword Final Stage  ,
# Required Data : Username (email or phone) , Token, new password, confirm new password
class UserForgotPasswordResetView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = UserForgotPasswordResetSerializer

    def post(self, request, format=None):
        serializer = UserForgotPasswordResetSerializer(data=request.data)

        if not serializer.is_valid():
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)

        # Get and validate request data
        username = serializer.validated_data.get('username').lower()
        token = serializer.validated_data.get('token')
        token = token.strip('"')

        password = serializer.validated_data.get('password')
        confirm_password = serializer.validated_data.get('confirm_password')

        if not validate_username(username):
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)
        # Validate password
        is_valid, message = validate_password(password)
        if not is_valid:
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=message)
        if password != confirm_password:
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.PASSWORD_CONFIRM_MISMATCH.value)
        # Determine username type and format the username
        username = User.get_formatted_username(username)

        try:
            # Try to retrieve the user based on the formatted username

            user = User.objects.get(**{User.get_username_type(username).lower(): username})
            # Check and delete the password reset token
            UserPasswordResetToken.objects.get(
                user=user,
                token=token,
                expire_at__lt=timezone.now()
            ).delete()

            # Set the new password, revoke all tokens, and save the user
            user.set_password(password)
            user.revoke_all_tokens()
            user.save()
            return BaseResponse(status=status.HTTP_200_OK,
                                message=ResponseMessage.RESET_PASSWORD_SUCCESSFULLY.value)
        except User.DoesNotExist:
            # User not found

            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)
        except UserPasswordResetToken.DoesNotExist:
            # Password reset token not found or expired

            return BaseResponse(status=status.HTTP_400_BAD_REQUEST,
                                message=ResponseMessage.FAILED.value)
