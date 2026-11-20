"""Django settings for Shellui Marketplace."""

from __future__ import annotations

import json
import os
import sys
import tomllib
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

from config.s3utils import (
    infer_addressing_style,
    infer_s3_region,
    normalize_custom_domain,
    normalize_s3_endpoint,
)

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


def _env_csv(name, default):
    raw = os.getenv(name, '').strip()
    if not raw:
        return list(default)
    return [item.strip() for item in raw.split(',') if item.strip()]


def _env_bool(name, default: bool) -> bool:
    raw = os.getenv(name, '').strip()
    if not raw:
        return default
    return raw.lower() in {'1', 'true', 'yes', 'on'}


def _env_int(name, default):
    raw = os.getenv(name, '').strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ImproperlyConfigured(f'{name} must be an integer. Got: {raw!r}') from exc


_secret_key = os.getenv('SECRET_KEY', '').strip()
if not _secret_key:
    raise ImproperlyConfigured(
        '\n'
        'SECRET_KEY is not set. marketplace-service cannot start.\n'
        '\n'
        'How to fix:\n'
        '  Local: cp .env.example .env, then set SECRET_KEY in .env.\n'
        '  Production: python manage.py generate_env --host market.example.com\n'
        '  prints every required setting with a fresh SECRET_KEY.\n'
    )
SECRET_KEY = _secret_key

DEBUG = _env_bool('DEBUG', False)
TEST_MODE = _env_bool('TEST_MODE', False) or 'test' in sys.argv
SETUP_TOKEN = os.getenv('SETUP_TOKEN', '').strip()
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG' if DEBUG else 'INFO').strip().upper() or (
    'DEBUG' if DEBUG else 'INFO'
)

ALLOWED_HOSTS = _env_csv('ALLOWED_HOSTS', ('localhost', '127.0.0.1', 'testserver'))
CSRF_TRUSTED_ORIGINS = _env_csv(
    'CSRF_TRUSTED_ORIGINS',
    (
        'http://localhost:8010',
        'http://127.0.0.1:8010',
        'http://localhost:5173',
        'http://127.0.0.1:5173',
    ),
)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
TRUST_PROXY = _env_bool('TRUST_PROXY', not DEBUG)


def _project_version():
    pyproject = BASE_DIR / 'pyproject.toml'
    with pyproject.open('rb') as fh:
        data = tomllib.load(fh)
    version = str(data.get('project', {}).get('version', '')).strip()
    if not version:
        raise ImproperlyConfigured(f'project.version is missing in {pyproject}')
    return version


VERSION = _project_version()

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'storages',
    'config.apps.ConfigConfig',
    'apps.catalog',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_THROTTLE_RATES': {
        'install': os.getenv('INSTALL_RATE', '30/min').strip() or '30/min',
    },
    'EXCEPTION_HANDLER': 'apps.catalog.exceptions.exception_handler',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Shellui Marketplace API',
    'DESCRIPTION': (
        'Public catalog for Shellui Marketplace. '
        'Every listing in 0.9 is free. '
        'Install and uninstall endpoints record anonymous or signed-in stats. '
        'They do not charge anyone and they do not start a checkout.'
    ),
    'VERSION': VERSION,
    'SERVE_INCLUDE_SCHEMA': False,
    'REDOC_DIST': 'SIDECAR',
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'TAGS': [
        {'name': 'catalog', 'description': 'Published apps and categories.'},
        {'name': 'stats', 'description': 'Install and uninstall counts.'},
        {'name': 'platform-metrics', 'description': 'Prometheus metrics.'},
        {'name': 'health', 'description': 'Service health checks.'},
    ],
}

MIDDLEWARE = [
    'config.request_context.RequestIdMiddleware',
    'config.health.LivenessMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
CSRF_FAILURE_VIEW = 'config.errors.csrf_failure'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

REDIS_URL = os.getenv('REDIS_URL', '').strip()
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'marketplace-service',
        }
    }

POSTGRES_DATABASE_URL = os.getenv('POSTGRES_DATABASE_URL', '').strip()
POSTGRES_SSL_REQUIRE = _env_bool('POSTGRES_SSL_REQUIRE', not DEBUG)

if POSTGRES_DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            POSTGRES_DATABASE_URL,
            conn_max_age=600,
            ssl_require=POSTGRES_SSL_REQUIRE,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.getenv('SQLITE_PATH', str(BASE_DIR / 'db.sqlite3')),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

if DEBUG:
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_AUTOREFRESH = True

MEDIA_URL = '/media/'
_media_root = os.getenv('MEDIA_ROOT', '').strip()
MEDIA_ROOT = Path(_media_root) if _media_root else (BASE_DIR / 'data' / 'media')

STORAGE_BACKEND = os.getenv('STORAGE_BACKEND', '').strip().lower() or 'filesystem'
if STORAGE_BACKEND not in {'s3', 'filesystem'}:
    raise ImproperlyConfigured(f'STORAGE_BACKEND must be "s3" or "filesystem". Got: {STORAGE_BACKEND!r}')

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '').strip()
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '').strip()
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', '').strip()
_raw_s3_endpoint = os.getenv('AWS_S3_ENDPOINT_URL', '').strip() or None
AWS_S3_ENDPOINT_URL = normalize_s3_endpoint(_raw_s3_endpoint, AWS_STORAGE_BUCKET_NAME)
AWS_S3_REGION_NAME = infer_s3_region(AWS_S3_ENDPOINT_URL, os.getenv('AWS_S3_REGION_NAME', 'us-east-1'))
AWS_S3_CUSTOM_DOMAIN = normalize_custom_domain(
    os.getenv('AWS_S3_CUSTOM_DOMAIN', '').strip() or None,
    AWS_S3_ENDPOINT_URL,
)
AWS_S3_SIGNATURE_VERSION = os.getenv('AWS_S3_SIGNATURE_VERSION', 's3v4').strip() or 's3v4'
AWS_S3_ADDRESSING_STYLE = infer_addressing_style(AWS_S3_ENDPOINT_URL, os.getenv('AWS_S3_ADDRESSING_STYLE', ''))
if AWS_S3_ADDRESSING_STYLE not in {'path', 'virtual', 'auto'}:
    raise ImproperlyConfigured(
        f'AWS_S3_ADDRESSING_STYLE must be path, virtual, or auto. Got: {AWS_S3_ADDRESSING_STYLE!r}'
    )

if STORAGE_BACKEND == 's3':
    if not AWS_STORAGE_BUCKET_NAME:
        raise ImproperlyConfigured('STORAGE_BACKEND=s3 requires AWS_STORAGE_BUCKET_NAME.')
    _default_storage = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'bucket_name': AWS_STORAGE_BUCKET_NAME,
            'region_name': AWS_S3_REGION_NAME,
            'access_key': AWS_ACCESS_KEY_ID or None,
            'secret_key': AWS_SECRET_ACCESS_KEY or None,
            'endpoint_url': AWS_S3_ENDPOINT_URL,
            'custom_domain': AWS_S3_CUSTOM_DOMAIN,
            'addressing_style': AWS_S3_ADDRESSING_STYLE,
            'default_acl': None,
            'querystring_auth': False,
            'file_overwrite': True,
            'signature_version': AWS_S3_SIGNATURE_VERSION,
            'location': 'marketplace',
        },
    }
else:
    _default_storage = {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
        'OPTIONS': {
            'location': str(MEDIA_ROOT),
            'base_url': MEDIA_URL,
        },
    }

STORAGES = {
    'default': _default_storage,
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

TEST_RUNNER = 'config.test_runner.IsolatedMediaDiscoverRunner'


def _parse_jwks_document(raw: str, *, source: str) -> dict:
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ImproperlyConfigured(f'{source} is not valid JSON: {exc}') from exc
    if not isinstance(document, dict) or not isinstance(document.get('keys'), list):
        raise ImproperlyConfigured(f'{source} must be a JWKS object with a "keys" array.')
    if not document['keys']:
        raise ImproperlyConfigured(f'{source} has an empty "keys" array.')
    return document


def _load_static_jwks() -> dict | None:
    file_path = os.getenv('IDENTITY_JWKS_FILE', '').strip()
    if file_path:
        path = Path(file_path)
        if not path.is_absolute():
            path = BASE_DIR / path
        if not path.is_file():
            raise ImproperlyConfigured(f'IDENTITY_JWKS_FILE not found: {path}')
        return _parse_jwks_document(path.read_text(encoding='utf-8'), source=str(path))
    raw = os.getenv('IDENTITY_JWKS', '').strip()
    if raw:
        return _parse_jwks_document(raw, source='IDENTITY_JWKS')
    return None


def _resolve_identity_jwks_url() -> str:
    explicit = os.getenv('IDENTITY_JWKS_URL', '').strip()
    if explicit:
        return explicit.rstrip('/')
    base = os.getenv('IDENTITY_SERVICE_URL', '').strip().rstrip('/')
    if base:
        return f'{base}/.well-known/jwks.json'
    return ''


IDENTITY_JWKS_DOCUMENT = _load_static_jwks()
IDENTITY_SERVICE_URL = os.getenv('IDENTITY_SERVICE_URL', '').strip().rstrip('/') or None
IDENTITY_JWKS_URL = '' if IDENTITY_JWKS_DOCUMENT is not None else _resolve_identity_jwks_url()
if IDENTITY_JWKS_URL and not IDENTITY_JWKS_URL.startswith(('http://', 'https://')):
    raise ImproperlyConfigured('IDENTITY_JWKS_URL must be an http or https URL.')
IDENTITY_ISSUER = os.getenv('IDENTITY_ISSUER', '').strip() or None
IDENTITY_AUDIENCE = os.getenv('IDENTITY_AUDIENCE', '').strip() or None

# Public catalog GETs are open. Install POSTs are credential-less JSON, so `*` is valid.
CORS_ALLOW_ALL_ORIGINS = _env_bool('CORS_ALLOW_ALL_ORIGINS', True)
CORS_ALLOWED_ORIGINS = _env_csv('CORS_ALLOWED_ORIGINS', ())
CORS_ALLOW_CREDENTIALS = False
CORS_ALLOW_METHODS = ['GET', 'HEAD', 'OPTIONS', 'POST']
CORS_ALLOW_HEADERS = [
    'accept',
    'authorization',
    'content-type',
    'x-request-id',
    'x-shellui-install-id',
]
CORS_URLS_REGEX = r'^/api/.*$'

CATALOG_CACHE_SECONDS = 0 if TEST_MODE else _env_int('CATALOG_CACHE_SECONDS', 60)
TRENDING_WINDOW_DAYS = _env_int('TRENDING_WINDOW_DAYS', 7)
PAGE_SIZE = _env_int('PAGE_SIZE', 24)
MAX_PAGE_SIZE = _env_int('MAX_PAGE_SIZE', 100)

DJANGO_ADMIN_ENABLED = _env_bool('DJANGO_ADMIN_ENABLED', True)

SECURE_SSL_REDIRECT = _env_bool('SECURE_SSL_REDIRECT', not DEBUG)
SESSION_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE', not DEBUG)
CSRF_COOKIE_SECURE = _env_bool('CSRF_COOKIE_SECURE', not DEBUG)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
if not DEBUG:
    SECURE_HSTS_SECONDS = _env_int('SECURE_HSTS_SECONDS', 31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

SENTRY_DSN = os.getenv('SENTRY_DSN', '').strip()
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment=os.getenv('SENTRY_ENVIRONMENT', '').strip() or None,
        release=os.getenv('SENTRY_RELEASE', '').strip() or VERSION,
        traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0') or 0),
        send_default_pii=False,
    )

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {'request_id': {'()': 'config.request_context.RequestIdFilter'}},
    'formatters': {
        'plain': {'format': '%(levelname)s %(name)s [%(request_id)s] %(message)s'},
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['request_id'],
            'formatter': 'plain',
        }
    },
    'root': {'handlers': ['console'], 'level': LOG_LEVEL},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
