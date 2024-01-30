from django.urls import path

from config.apps.content.views import front

urlpatterns = [
    path(
        "home/data/",
        front.GetHomeDataView.as_view(),
        name="content_get_home_data",
    ),
]
