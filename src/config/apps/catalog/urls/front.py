from django.urls import path

from config.apps.catalog.views import front

urlpatterns = [
    path("search-header/", front.CatalogSearchView.as_view(), name="catalog-search"),
    path("search/", front.ProductSearchView.as_view(), name="search"),
    path(
        "search/filter/options/",
        front.SearchFilterOptionView.as_view(),
        name="search-filter-options",
    ),
    path(
        "product/<int:short_slug>/",
        front.ProductDetailView.as_view(),
        name="product-detail",
    ),
    path("product/visit/logged-in/", front.ProductVisitLoggedInView.as_view(), name="product_visit_logged_in"),
    path("product/visit/anonymous/", front.ProductVisitAnonymousView.as_view(), name="product_visit_anonymous"),
    path(
        "product/comment/list/<int:product_id>/",
        front.ProductCommentListAPIView.as_view(),
        name="product-comment-list",
    ),
    path(
        "product/comment/create/",
        front.ProductCommentCreateAPIView.as_view(),
        name="product-comment-create",
    ),
]
