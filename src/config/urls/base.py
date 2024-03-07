from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

admin.autodiscover()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("config.api.urls")),
]
if settings.LOCAL_STORAGE:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
