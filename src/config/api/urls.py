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
        "address/",
        include(
            ("config.apps.user.address.urls.front", "config.apps.user.address"),
            namespace="address_front",
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
    path(
        "content/",
        include(
            ("config.apps.content.urls.front", "config.apps.content"),
            namespace="content_front",
        ),
    ),
    path(
        "order/",
        include(
            ("config.apps.order.urls.front", "config.apps.order"),
            namespace="order_front",
        ),
    ),
    path(
        "transaction/",
        include(
            ("config.apps.transaction.urls.front", "config.apps.transaction"),
            namespace="transaction_front",
        ),
    ),
]

urlpatterns = [] + admin_urls + front_urls
