from django.urls import include, path

admin_urls = [
    path('api/admin/users/',
         include(('config.apps.user.account.urls.admin', 'config.apps.user.account'), namespace='users-admin')),
]

front_urls = [
    path('api/users/',
         include(('config.apps.user.account.urls.front', 'config.apps.user.account'), namespace='users-front')),
]

urlpatterns = [] + admin_urls + front_urls
