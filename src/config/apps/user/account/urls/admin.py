from django.urls import path
from rest_framework_simplejwt import views as jwt_views

from config.apps.user.account.views import admin

urlpatterns = [

    path("token/", jwt_views.TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", jwt_views.TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", admin.UserLogoutAdminView.as_view(), name="user_logout"),
    path(
        "request/current/",
        admin.RequestCurrentUserAdminView.as_view(),
        name="user_request_current_detail",
    ),
    # Authenticate
    path(
        "authenticate/check/",
        admin.UserAuthenticationCheckAdminView.as_view(),
        name="user_authenticate_check",
    ),
    path(
        "authenticate/password/",
        admin.UserPasswordAuthenticationAdminView.as_view(),
        name="user_authenticate_password",
    ),
    path(
        "authenticate/otp/",
        admin.UserOTPAuthenticationAdminView.as_view(),
        name="user_authenticate_otp",
    ),
    # Forgot password
    path(
        "forgot/password/check/",
        admin.UserForgotPasswordCheckAdminView.as_view(),
        name="user_forgot_password_check",
    ),
    path(
        "forgot/password/otp/",
        admin.UserForgotPasswordOTPAdminView.as_view(),
        name="user_forgot_password_otp",
    ),
    path(
        "forgot/password/reset/",
        admin.UserForgotPasswordResetAdminView.as_view(),
        name="user_forgot_password_otp",
    ),
    # # User Detail
    path("edit/detail/", admin.UserUpdateDetailAdminView.as_view(), name="user_edit_detail"),
    path("edit/password/", admin.UserEditPasswordAdminView.as_view(), name="user_edit_password"),
    path(
        "edit/phone/request/",
        admin.UserEditPhoneRequestAdminView.as_view(),
        name="user_edit_phone_request",
    ),
    path(
        "edit/phone/confirm/",
        admin.UserEditPhoneConfirmAdminView.as_view(),
        name="user_edit_phone_confirm",
    ),
    path(
        "edit/email/request/",
        admin.UserEditEmailRequestAdminView.as_view(),
        name="user_edit_email_request",
    ),
    path(
        "edit/email/confirm/",
        admin.UserEditEmailConfirmAdminView.as_view(),
        name="user_edit_email_confirm",
    ),
]
