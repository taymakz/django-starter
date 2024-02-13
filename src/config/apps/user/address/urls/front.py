from django.urls import path

from config.apps.user.address.views import front

urlpatterns = [
    path('', front.UserAddressAPIView.as_view(), name='user_address'),
    path('/get/<int:pk>/', front.UserAddressDetailAPIView.as_view(), name='user_address_detail'),

]
