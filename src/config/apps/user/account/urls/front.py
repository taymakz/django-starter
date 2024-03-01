from django.urls import path
from rest_framework_simplejwt import views as jwt_views

from config.apps.user.account.views import front

urlpatterns = [
    path("token/", jwt_views.TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", jwt_views.TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", front.UserLogoutView.as_view(), name="user_logout"),
    path(
        "request/current/",
        front.RequestCurrentUserView.as_view(),
        name="user_request_current_detail",
    ),
    # Authenticate
    path(
        "authenticate/check/",
        front.UserAuthenticationCheckView.as_view(),
        name="user_authenticate_check",
    ),
    path(
        "authenticate/password/",
        front.UserPasswordAuthenticationView.as_view(),
        name="user_authenticate_password",
    ),
    path(
        "authenticate/otp/",
        front.UserOTPAuthenticationView.as_view(),
        name="user_authenticate_otp",
    ),
    # Forgot password
    path(
        "forgot/password/check/",
        front.UserForgotPasswordCheckView.as_view(),
        name="user_forgot_password_check",
    ),
    path(
        "forgot/password/otp/",
        front.UserForgotPasswordOTPView.as_view(),
        name="user_forgot_password_otp",
    ),
    path(
        "forgot/password/reset/",
        front.UserForgotPasswordResetView.as_view(),
        name="user_forgot_password_otp",
    ),
    path(
        "favorite/",
        front.UserFavoriteProductView.as_view(),
        name="user_favorite_product",
    ),
    path(
        "favorite/clear/",
        front.UserFavoriteProductClearView.as_view(),
        name="user_favorite_product_clear",
    ),
    path(
        "recent-product/",
        front.UserRecentVisitedProductView.as_view(),
        name="user_recent_product",
    ),
    path(
        "recent-product/clear/",
        front.UserRecentVisitedProductClearView.as_view(),
        name="user_recent_product_clear",
    ),
    path(
        "search-history/",
        front.UserSearchHistoryView.as_view(),
        name="user_search_history",
    ),
    # User Detail
    path('edit/detail/', front.UserUpdateDetailView.as_view(), name='user_edit_detail'),
    path('edit/password/', front.UserEditPassword.as_view(), name='user_edit_password'),

    path('edit/phone/request/', front.UserEditPhoneRequestView.as_view(), name='user_edit_phone_request'),
    path('edit/phone/confirm/', front.UserEditPhoneConfirmView.as_view(), name='user_edit_phone_confirm'),

    path('edit/email/request/', front.UserEditEmailRequestView.as_view(), name='user_edit_email_request'),
    path('edit/email/confirm/', front.UserEditEmailConfirmView.as_view(), name='user_edit_email_confirm'),

]
