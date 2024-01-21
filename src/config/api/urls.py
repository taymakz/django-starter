from django.urls import include, path

admin_urls = [
    path('api/admin/users/',
         include(('config.apps.auths.account.urls.admin', 'config.apps.auths.account'), namespace='users-admin')),
]

front_urls = [
    path('api/users/',
         include(('config.apps.auths.account.urls.front', 'config.apps.auths.account'), namespace='users-front')),
]

urlpatterns = [] + admin_urls + front_urls
