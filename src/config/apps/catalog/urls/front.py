from django.urls import path

from config.apps.catalog.views import front

urlpatterns = [
    path('search/', front.ProductSearchView.as_view(), name='search'),
    path('search/filter/options/', front.SearchFilterOptionView.as_view(), name='search-filter-options')
]
