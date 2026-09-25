from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

handler404 = 'gesso.web.views.errors.not_found'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gesso.web.urls')),
    path('', include('gesso.commerce.urls')),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]
