from django.urls import include, path

admin_urls = [
    path(
        "admin/users/",
        include(
            ("config.apps.user.account.urls.admin", "config.apps.user.account"),
            namespace="users_admin",
        ),
    ),
    path(
        "admin/messages/verification/",
        include(
            (
                "config.apps.messages.verification.urls.admin",
                "config.apps.messages.verification",
            ),
            namespace="messages_verification_admin",
        ),
    ),
]

front_urls = [
    path(
        "users/",
        include(
            ("config.apps.user.account.urls.front", "config.apps.user.account"),
            namespace="users_front",
        ),
    ),
    path(
        "messages/verification/",
        include(
            (
                "config.apps.messages.verification.urls.front",
                "config.apps.messages.verification",
            ),
            namespace="messages_verification_front",
        ),
    ),
    path(
        "catalog/",
        include(
            ("config.apps.catalog.urls.front", "config.apps.catalog"),
            namespace="catalog_front",
        ),
    ),
]

urlpatterns = [] + admin_urls + front_urls
