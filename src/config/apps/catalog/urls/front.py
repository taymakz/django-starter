from django.urls import path

from config.apps.catalog.views import front

urlpatterns = [
    path(
        "header/data/",
        front.GetHeaderDataView.as_view(),
        name="catalog_get_header_data",
    ),
]
