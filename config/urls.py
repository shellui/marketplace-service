"""URL configuration for Shellui Marketplace."""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from django.views.decorators.clickjacking import xframe_options_exempt
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from apps.catalog.admin import admin_site
from apps.catalog.views import AppDetailView, AppListView, CategoryListView, InstallView, UninstallView

from . import views
from .health import ready

urlpatterns = [
    path('', views.root, name='root'),
    path('health/ready', ready, name='health-ready'),
    path('api/apps', AppListView.as_view(), name='app-list'),
    path('api/categories', CategoryListView.as_view(), name='category-list'),
    re_path(r'^api/apps/(?P<slug>.+)/install/?$', InstallView.as_view(), name='app-install'),
    re_path(r'^api/apps/(?P<slug>.+)/uninstall/?$', UninstallView.as_view(), name='app-uninstall'),
    re_path(r'^api/apps/(?P<slug>[^/]+(?:/[^/]+)?)/?$', AppDetailView.as_view(), name='app-detail'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        xframe_options_exempt(SpectacularSwaggerView.as_view(url_name='schema')),
        name='swagger-ui',
    ),
    path(
        'api/docs/redoc/',
        xframe_options_exempt(SpectacularRedocView.as_view(url_name='schema')),
        name='redoc',
    ),
    path('', include('apps.catalog.urls')),
]

if settings.DJANGO_ADMIN_ENABLED:
    urlpatterns.insert(1, path('admin/', admin_site.urls))

if settings.DEBUG and settings.STORAGE_BACKEND != 's3':
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = 'config.errors.bad_request'
handler403 = 'config.errors.permission_denied'
handler404 = 'config.errors.page_not_found'
handler500 = 'config.errors.server_error'
