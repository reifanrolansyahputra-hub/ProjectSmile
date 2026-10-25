from django.contrib import admin
from django.urls import path, include
from core.views import home
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("", include("accounts.urls")),
    path("", include("portal.urls")),
    path("", include("materi.urls")),
    path("", include("akademik.urls")),
    path("", include("pembayaran.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)