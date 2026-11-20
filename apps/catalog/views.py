"""Public catalog and install stat endpoints."""

from __future__ import annotations

import functools
import json
import logging
from urllib.parse import unquote

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth import OptionalIdentityAuthentication
from .models import App, AppInstall, Category
from .queries import published_apps, trending_ids, trending_scores
from .serializers import (
    AppDetailResponseSerializer,
    AppListResponseSerializer,
    CategoryListResponseSerializer,
    InstallRequestSerializer,
    InstallResponseSerializer,
    category_data,
    public_app_data,
)
from .stats import record_install, record_uninstall
from .subjects import anonymous_subject, user_subject
from .throttling import InstallRateThrottle
from .validation import validate_install_id, validate_origin, validate_slug

logger = logging.getLogger(__name__)

_SORTS = {
    'popular': ('-install_total', 'name'),
    'recent': ('-catalog_updated_on', '-install_total', 'name'),
    'name': ('name',),
}


def _catalog_cache(view):
    @functools.wraps(view)
    def wrapped(self, request, *args, **kwargs):
        if settings.CATALOG_CACHE_SECONDS <= 0:
            return view(self, request, *args, **kwargs)

        def inner(req, *inner_args, **inner_kwargs):
            return view(self, req, *inner_args, **inner_kwargs)

        return cache_page(settings.CATALOG_CACHE_SECONDS)(inner)(request, *args, **kwargs)

    return wrapped


def _decode_slug(raw: str) -> str:
    return unquote(raw or '').strip().strip('/')


def _install_total(app: App) -> int:
    active = getattr(app, 'active_installs', None)
    if active is None:
        active = app.installs.filter(active=True).count()
    return int(app.baseline_installs) + int(active)


def _payload(app: App, scores: dict[int, int], hot: set[int]) -> dict | None:
    score = scores.get(app.id, 0)
    return public_app_data(
        app,
        install_count=_install_total(app),
        trending_score=score,
        trending=app.id in hot,
    )


_CATALOG_PARAMS = [
    OpenApiParameter(name='q', type=str, required=False),
    OpenApiParameter(name='category', type=str, required=False),
    OpenApiParameter(name='official', type=str, required=False, enum=['true', 'false']),
    OpenApiParameter(name='sort', type=str, required=False, enum=['popular', 'recent', 'name']),
    OpenApiParameter(name='page', type=int, required=False),
    OpenApiParameter(name='page_size', type=int, required=False),
]


class AppListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = AppListResponseSerializer

    @_catalog_cache
    @extend_schema(
        operation_id='catalog_apps_list',
        parameters=_CATALOG_PARAMS,
        responses={200: AppListResponseSerializer},
    )
    def get(self, request):
        sort = request.query_params.get('sort', 'popular')
        if sort not in _SORTS:
            return Response({'detail': 'sort must be popular, recent, or name.'}, status=400)
        try:
            page = int(request.query_params.get('page', '1'))
            page_size = int(request.query_params.get('page_size', str(settings.PAGE_SIZE)))
        except ValueError:
            return Response({'detail': 'page and page_size must be integers.'}, status=400)
        if page < 1 or page_size < 1 or page_size > settings.MAX_PAGE_SIZE:
            return Response({'detail': 'page or page_size is out of range.'}, status=400)

        qs = published_apps()
        category = (request.query_params.get('category') or '').strip()
        if category:
            qs = qs.filter(category__slug=category)
        official = (request.query_params.get('official') or '').strip().lower()
        if official in {'1', 'true', 'yes'}:
            qs = qs.filter(is_official=True)
        elif official in {'0', 'false', 'no'}:
            qs = qs.filter(is_official=False)
        elif official:
            return Response({'detail': 'official must be true or false.'}, status=400)
        query = (request.query_params.get('q') or '').strip()
        if query:
            qs = qs.filter(_search(query))
        qs = qs.order_by(*_SORTS[sort], 'id')
        total = qs.count()
        start = (page - 1) * page_size
        rows = list(qs[start : start + page_size])
        scores = trending_scores()
        hot = trending_ids(scores)
        apps = []
        for app in rows:
            data = _payload(app, scores, hot)
            if data is not None:
                apps.append(data)
        next_page = page + 1 if start + page_size < total else None
        previous = page - 1 if page > 1 else None
        response = Response(
            {
                'apps': apps,
                'count': total,
                'page': page,
                'pageSize': page_size,
                'next': next_page,
                'previous': previous,
            }
        )
        if settings.CATALOG_CACHE_SECONDS > 0:
            response['Cache-Control'] = f'public, max-age={settings.CATALOG_CACHE_SECONDS}'
        return response


def _search(query: str):
    return (
        Q(name__icontains=query)
        | Q(tagline__icontains=query)
        | Q(slug__icontains=query)
        | Q(publisher_name__icontains=query)
        | Q(description__icontains=query)
        | Q(tags__icontains=query)
    )


class AppDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = AppDetailResponseSerializer

    @_catalog_cache
    @extend_schema(operation_id='catalog_apps_retrieve', responses={200: AppDetailResponseSerializer})
    def get(self, request, slug):
        decoded = _decode_slug(slug)
        try:
            validate_slug(decoded)
        except ValidationError:
            return Response({'detail': 'Not found.'}, status=404)
        app = published_apps().filter(slug=decoded).first()
        if app is None:
            return Response({'detail': 'Not found.'}, status=404)
        scores = trending_scores()
        data = _payload(app, scores, trending_ids(scores))
        if data is None:
            return Response({'detail': 'Not found.'}, status=404)
        response = Response({'app': data})
        if settings.CATALOG_CACHE_SECONDS > 0:
            response['Cache-Control'] = f'public, max-age={settings.CATALOG_CACHE_SECONDS}'
        return response


class CategoryListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = CategoryListResponseSerializer

    @_catalog_cache
    @extend_schema(operation_id='catalog_categories_list', responses={200: CategoryListResponseSerializer})
    def get(self, request):
        categories = Category.objects.filter(apps__status=App.STATUS_PUBLISHED).distinct().order_by('position', 'label')
        response = Response({'categories': [category_data(category) for category in categories]})
        if settings.CATALOG_CACHE_SECONDS > 0:
            response['Cache-Control'] = f'public, max-age={settings.CATALOG_CACHE_SECONDS}'
        return response


class _StatMixin:
    authentication_classes = [OptionalIdentityAuthentication]
    permission_classes = [AllowAny]
    throttle_classes = [InstallRateThrottle]

    def _json_object(self, request):
        content_type = (request.content_type or '').split(';')[0].strip().lower()
        if content_type != 'application/json':
            return None, Response({'detail': 'Content-Type must be application/json.'}, status=415)
        raw = request.body or b'{}'
        if not raw.strip():
            raw = b'{}'
        try:
            payload = json.loads(raw.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None, Response({'detail': 'Body must be a JSON object.'}, status=400)
        if not isinstance(payload, dict):
            return None, Response({'detail': 'Body must be a JSON object.'}, status=400)
        extra = set(payload) - {'installId'}
        if extra:
            return None, Response({'detail': 'Unexpected fields in install body.'}, status=400)
        return payload, None

    def _subject(self, request, payload):
        origin_header = request.headers.get('Origin')
        origin = None
        if origin_header is not None and origin_header != '':
            try:
                origin = validate_origin(origin_header)
            except ValidationError:
                return None, None, Response({'detail': 'invalid_origin'}, status=400)
        user = request.user if getattr(request.user, 'is_authenticated', False) else None
        if user is not None and getattr(user, 'sub', None):
            return user_subject(user.sub), AppInstall.KIND_USER, None
        if origin is None:
            return None, None, None
        header_id = request.headers.get('X-Shellui-Install-Id', '')
        body_id = payload.get('installId', '')
        if header_id and body_id and header_id != body_id:
            return None, None, Response({'detail': 'invalid_install_id'}, status=400)
        raw_id = body_id or header_id
        if not raw_id:
            return None, None, None
        try:
            install_id = validate_install_id(raw_id)
        except ValidationError:
            return None, None, Response({'detail': 'invalid_install_id'}, status=400)
        return anonymous_subject(origin, install_id), AppInstall.KIND_ANONYMOUS, None

    def _app(self, slug):
        decoded = _decode_slug(slug)
        try:
            validate_slug(decoded)
        except ValidationError:
            return None
        return published_apps().filter(slug=decoded).first()


@method_decorator(csrf_exempt, name='dispatch')
class InstallView(_StatMixin, APIView):
    serializer_class = InstallResponseSerializer

    @extend_schema(
        operation_id='catalog_apps_install',
        request=InstallRequestSerializer,
        responses={200: InstallResponseSerializer},
    )
    def post(self, request, slug):
        payload, error = self._json_object(request)
        if error is not None:
            return error
        app = self._app(slug)
        if app is None:
            return Response({'detail': 'Not found.'}, status=404)
        subject, kind, error = self._subject(request, payload)
        if error is not None:
            return error
        if subject is None:
            return Response(
                {
                    'ok': True,
                    'counted': False,
                    'active': False,
                    'installCount': _install_total(app),
                    'reason': 'dedupe_key_required',
                }
            )
        record_install(app=app, subject_hash=subject, kind=kind)
        app = published_apps().filter(pk=app.pk).first()
        active = AppInstall.objects.filter(app=app, subject_hash=subject, active=True).exists()
        logger.info('install ping app=%s counted=%s', app.slug, True)
        return Response(
            {
                'ok': True,
                'counted': True,
                'active': active,
                'installCount': _install_total(app),
            }
        )


@method_decorator(csrf_exempt, name='dispatch')
class UninstallView(_StatMixin, APIView):
    serializer_class = InstallResponseSerializer

    @extend_schema(
        operation_id='catalog_apps_uninstall',
        request=InstallRequestSerializer,
        responses={200: InstallResponseSerializer},
    )
    def post(self, request, slug):
        payload, error = self._json_object(request)
        if error is not None:
            return error
        app = self._app(slug)
        if app is None:
            return Response({'detail': 'Not found.'}, status=404)
        subject, _kind, error = self._subject(request, payload)
        if error is not None:
            return error
        if subject is None:
            return Response(
                {
                    'ok': True,
                    'counted': False,
                    'active': False,
                    'installCount': _install_total(app),
                    'reason': 'dedupe_key_required',
                }
            )
        record_uninstall(app=app, subject_hash=subject)
        app = published_apps().filter(pk=app.pk).first()
        active = AppInstall.objects.filter(app=app, subject_hash=subject, active=True).exists()
        return Response(
            {
                'ok': True,
                'counted': True,
                'active': active,
                'installCount': _install_total(app),
            }
        )
