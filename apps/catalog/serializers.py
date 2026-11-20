"""Public catalog JSON. Shapes match the directory client and `shellui add`."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers

from .models import App, AppVersion, Category
from .validation import AUTH_CAPABILITY, PUBLIC_CAPABILITIES, validate_absolute_url, validate_nav_template


class CategorySerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()


class PublisherSerializer(serializers.Serializer):
    name = serializers.CharField()
    kind = serializers.ChoiceField(choices=['official', 'verified', 'community'])
    url = serializers.CharField(required=False, allow_blank=True)


class NavigationSerializer(serializers.Serializer):
    label = serializers.CharField()
    path = serializers.CharField()
    url = serializers.CharField()
    icon = serializers.CharField()


class ScreenshotSerializer(serializers.Serializer):
    src = serializers.CharField()
    alt = serializers.CharField()


class AppSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    tagline = serializers.CharField()
    description = serializers.CharField()
    publisher = PublisherSerializer()
    category = serializers.CharField()
    version = serializers.CharField()
    homepage = serializers.CharField()
    support = serializers.CharField()
    icon = serializers.CharField()
    screenshots = ScreenshotSerializer(many=True)
    installCount = serializers.IntegerField()
    updatedAt = serializers.CharField()
    featured = serializers.BooleanField()
    capabilities = serializers.ListField(child=serializers.CharField())
    navigation = NavigationSerializer()
    tags = serializers.ListField(child=serializers.CharField())
    official = serializers.BooleanField()
    url = serializers.CharField()
    path = serializers.CharField()
    safeForAuthToken = serializers.BooleanField()
    trending = serializers.BooleanField()
    trendingScore = serializers.IntegerField()


class AppListResponseSerializer(serializers.Serializer):
    apps = AppSerializer(many=True)
    count = serializers.IntegerField()
    page = serializers.IntegerField()
    pageSize = serializers.IntegerField()
    next = serializers.IntegerField(allow_null=True)
    previous = serializers.IntegerField(allow_null=True)


class AppDetailResponseSerializer(serializers.Serializer):
    app = AppSerializer()


class CategoryListResponseSerializer(serializers.Serializer):
    categories = CategorySerializer(many=True)


class InstallRequestSerializer(serializers.Serializer):
    installId = serializers.CharField(required=False)


class InstallResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    counted = serializers.BooleanField()
    active = serializers.BooleanField()
    installCount = serializers.IntegerField()
    reason = serializers.CharField(required=False)


def _latest_version(app: App) -> AppVersion | None:
    cache = getattr(app, '_prefetched_objects_cache', {})
    if 'versions' in cache:
        versions = list(app.versions.all())
        return versions[0] if versions else None
    return app.versions.order_by('-created_at', '-id').first()


def _public_capabilities(app: App) -> list[str]:
    allowed = set(PUBLIC_CAPABILITIES)
    if app.is_official:
        allowed.add(AUTH_CAPABILITY)
    seen = []
    for item in app.capabilities or []:
        if item in allowed and item not in seen:
            seen.append(item)
    return seen


def _navigation(app: App) -> dict | None:
    version = _latest_version(app)
    raw = None
    if version is not None and version.nav_template:
        raw = version.nav_template
    elif app.nav_template:
        raw = app.nav_template
    if not isinstance(raw, dict):
        return None
    try:
        cleaned = validate_nav_template(raw, official=app.is_official)
        validate_absolute_url(cleaned['url'], field='Navigation url')
    except ValidationError:
        return None
    if not app.is_official:
        cleaned.pop('safeForAuthToken', None)
    elif 'auth' not in _public_capabilities(app):
        cleaned.pop('safeForAuthToken', None)
    return cleaned


def _media_src(file_field, fallback: str) -> str:
    if file_field:
        url = file_field.url
        if url.startswith(('https://', '/')):
            return url
        if url.startswith('http://'):
            try:
                validate_absolute_url(url, field='Media')
            except ValidationError:
                return fallback
            return url
        return url
    return fallback


def _screenshots(app: App) -> list[dict]:
    shots = []
    for shot in app.screenshots.all():
        src = _media_src(shot.image, shot.src)
        alt = (shot.alt or '').strip()
        if not src or not alt:
            continue
        if src.startswith('http://'):
            try:
                validate_absolute_url(src, field='Screenshot')
            except ValidationError:
                continue
        shots.append({'src': src, 'alt': alt})
    return shots


def public_app_data(app: App, *, install_count: int, trending_score: int, trending: bool) -> dict | None:
    navigation = _navigation(app)
    if navigation is None:
        return None
    capabilities = _public_capabilities(app)
    if not capabilities:
        return None
    icon = _media_src(app.icon, app.icon_url)
    if not icon:
        return None
    safe = bool(navigation.get('safeForAuthToken')) and app.is_official and AUTH_CAPABILITY in capabilities
    publisher = {'name': app.publisher_name, 'kind': app.publisher_kind}
    if app.publisher_url:
        publisher['url'] = app.publisher_url
    version = _latest_version(app)
    updated = app.catalog_updated_on or timezone.now().date()
    return {
        'slug': app.slug,
        'name': app.name,
        'tagline': app.tagline,
        'description': app.description,
        'publisher': publisher,
        'category': app.category.slug,
        'version': version.version if version else '0.0.0',
        'homepage': app.homepage_url,
        'support': app.support_url,
        'icon': icon,
        'screenshots': _screenshots(app),
        'installCount': install_count,
        'updatedAt': updated.isoformat(),
        'featured': bool(app.featured or app.is_official),
        'capabilities': capabilities,
        'navigation': {
            'label': navigation['label'],
            'path': navigation['path'],
            'url': navigation['url'],
            'icon': navigation['icon'],
        },
        'tags': list(app.tags or []),
        'official': app.is_official,
        'url': navigation['url'],
        'path': navigation['path'],
        'safeForAuthToken': safe,
        'trending': trending,
        'trendingScore': trending_score,
    }


def category_data(category: Category) -> dict:
    return {'id': category.slug, 'label': category.label}
