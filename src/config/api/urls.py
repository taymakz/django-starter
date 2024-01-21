from django.urls import include, path

admin_urls = [
    path('admin/users/',
         include(('config.apps.user.account.urls.admin', 'config.apps.user.account'), namespace='users_admin')),
]

front_urls = [
    path('users/',
         include(('config.apps.user.account.urls.front', 'config.apps.user.account'), namespace='users_front')),
]

urlpatterns = [] + admin_urls + front_urls
