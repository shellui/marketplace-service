"""Catalog field rules: HTTPS URLs, navigation templates, and the capability whitelist."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError

PUBLIC_CAPABILITIES = ('theme', 'locale', 'ui', 'navigate', 'storage', 'ai')
AUTH_CAPABILITY = 'auth'
ALLOWED_CAPABILITIES = frozenset((*PUBLIC_CAPABILITIES, AUTH_CAPABILITY))

SLUG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)?$')
TAG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
VERSION_RE = re.compile(r'^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.]+)?$')
ICON_NAME_RE = re.compile(r'^[a-z0-9][a-z0-9-]{0,40}$')
RELATIVE_PATH_RE = re.compile(r'^/[A-Za-z0-9][A-Za-z0-9._/-]{0,240}$')
NAV_PATH_RE = re.compile(r'^/?[A-Za-z0-9][A-Za-z0-9/_-]{0,120}$')
INSTALL_ID_RE = re.compile(r'^[A-Za-z0-9_-]{8,128}$')
HOST_RE = re.compile(
    r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$'
)
IPV4_RE = re.compile(r'^(?:\d{1,3}\.){3}\d{1,3}$')

NAV_KEYS = frozenset({'label', 'path', 'url', 'icon', 'safeForAuthToken'})
_LOCAL_HOSTS = frozenset({'localhost', '127.0.0.1'})


def _debug() -> bool:
    return bool(getattr(settings, 'DEBUG', False))


def validate_slug(value: str) -> str:
    slug = (value or '').strip()
    if not SLUG_RE.fullmatch(slug) or len(slug) > 80:
        raise ValidationError('Slug must look like files or shellui/files (lowercase, one slash at most).')
    return slug


def validate_tags(value) -> list[str]:
    if value in (None, ''):
        return []
    if not isinstance(value, list):
        raise ValidationError('Tags must be a list of short labels.')
    if len(value) > 12:
        raise ValidationError('An app can have at most 12 tags.')
    seen = []
    for item in value:
        if not isinstance(item, str) or not TAG_RE.fullmatch(item) or len(item) > 32:
            raise ValidationError('Each tag must be a lowercase label such as storage.')
        if item not in seen:
            seen.append(item)
    return seen


def validate_version(value: str) -> str:
    version = (value or '').strip()
    if not VERSION_RE.fullmatch(version):
        raise ValidationError('Version must look like 1.2.3.')
    return version


def _is_local_http(parts) -> bool:
    host = (parts.hostname or '').lower()
    return parts.scheme == 'http' and host in _LOCAL_HOSTS


def validate_absolute_url(value: str, *, field: str = 'URL') -> str:
    """HTTPS only. http://localhost is allowed when DEBUG is true."""
    text = (value or '').strip()
    if not text or any(char in text for char in ' \t\r\n\\'):
        raise ValidationError(f'{field} must be an absolute https URL.')
    lowered = text.lower()
    if lowered.startswith(('javascript:', 'data:', 'vbscript:', 'file:')):
        raise ValidationError(f'{field} must be an absolute https URL.')
    parts = urlsplit(text)
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ValidationError(f'{field} must not include credentials, a query, or a fragment.')
    if parts.scheme == 'https':
        pass
    elif _debug() and _is_local_http(parts):
        pass
    else:
        raise ValidationError(f'{field} must use https.')
    host = (parts.hostname or '').lower()
    if not host or not (HOST_RE.fullmatch(host) or IPV4_RE.fullmatch(host)):
        raise ValidationError(f'{field} has a host this service will not publish.')
    if parts.port is not None and not (1 <= parts.port <= 65535):
        raise ValidationError(f'{field} has a port this service will not publish.')
    port = f':{parts.port}' if parts.port else ''
    path = parts.path or ''
    if path == '/':
        path = '/'
    return f'{parts.scheme}://{host}{port}{path}'


def validate_optional_url(value: str, *, field: str = 'URL') -> str:
    if not (value or '').strip():
        return ''
    return validate_absolute_url(value, field=field)


def validate_icon_reference(value: str, *, field: str = 'Icon') -> str:
    """Icon name, site-relative path, or https URL. Empty is allowed when a file is uploaded."""
    text = (value or '').strip()
    if not text:
        return ''
    if text.startswith('/'):
        if '..' in text or not RELATIVE_PATH_RE.fullmatch(text):
            raise ValidationError(f'{field} path must stay inside the site and cannot contain "..".')
        return text
    if ICON_NAME_RE.fullmatch(text):
        return text
    return validate_absolute_url(text, field=field)


def validate_capabilities(value, *, official: bool) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValidationError('Choose at least one capability.')
    seen: list[str] = []
    for item in value:
        if not isinstance(item, str) or item not in ALLOWED_CAPABILITIES:
            allowed = ', '.join(PUBLIC_CAPABILITIES)
            raise ValidationError(f'Capabilities must be chosen from: {allowed}. auth is official apps only.')
        if item == AUTH_CAPABILITY and not official:
            raise ValidationError('Only an official Shellui app can request the auth capability.')
        if item not in seen:
            seen.append(item)
    return seen


def validate_nav_template(value, *, official: bool) -> dict:
    if not isinstance(value, dict):
        raise ValidationError('Navigation template must be a JSON object.')
    extra = set(value) - NAV_KEYS
    if extra:
        names = ', '.join(sorted(extra))
        raise ValidationError(f'Navigation template has unsupported fields: {names}.')
    label = value.get('label')
    path = value.get('path')
    url = value.get('url')
    icon = value.get('icon')
    if not isinstance(label, str) or not label.strip() or len(label.strip()) > 80:
        raise ValidationError('Navigation label must be 1 to 80 characters.')
    if any(ord(char) < 32 or char in '<>' for char in label):
        raise ValidationError('Navigation label must be plain text.')
    if not isinstance(path, str) or not NAV_PATH_RE.fullmatch(path.strip()) or '..' in path:
        raise ValidationError('Navigation path must be a short path such as /files.')
    if not isinstance(url, str):
        raise ValidationError('Navigation url must be an https URL.')
    cleaned_url = validate_absolute_url(url, field='Navigation url')
    if not isinstance(icon, str) or not icon.strip():
        raise ValidationError('Navigation icon is required.')
    cleaned_icon = validate_icon_reference(icon, field='Navigation icon')
    wants_auth = value.get('safeForAuthToken', False)
    if wants_auth is not False and not isinstance(wants_auth, bool):
        raise ValidationError('safeForAuthToken must be true or false.')
    if wants_auth and not official:
        raise ValidationError('Only an official Shellui app can set safeForAuthToken.')
    cleaned = {
        'label': label.strip(),
        'path': path.strip(),
        'url': cleaned_url,
        'icon': cleaned_icon,
    }
    if wants_auth:
        cleaned['safeForAuthToken'] = True
    return cleaned


def validate_origin(value: str) -> str:
    """Browser Origin header: https://host[:port], or http://localhost[:port] in DEBUG."""
    text = (value or '').strip()
    if not text or text.lower() == 'null' or any(char in text for char in ' \t\r\n\\'):
        raise ValidationError('Origin must be an https origin.')
    parts = urlsplit(text)
    if parts.username or parts.password or parts.query or parts.fragment or parts.path not in {'', '/'}:
        raise ValidationError('Origin must be scheme, host, and optional port only.')
    if parts.scheme == 'https' or (_debug() and _is_local_http(parts)):
        host = (parts.hostname or '').lower()
    else:
        raise ValidationError('Origin must use https.')
    if not host or not (HOST_RE.fullmatch(host) or IPV4_RE.fullmatch(host)):
        raise ValidationError('Origin host is not allowed.')
    if host in _LOCAL_HOSTS and not _debug():
        raise ValidationError('Localhost origins are only accepted when DEBUG is true.')
    if parts.port is not None and not (1 <= parts.port <= 65535):
        raise ValidationError('Origin port is not allowed.')
    port = f':{parts.port}' if parts.port else ''
    return f'{parts.scheme}://{host}{port}'


def validate_install_id(value: str) -> str:
    text = (value or '').strip()
    if not INSTALL_ID_RE.fullmatch(text):
        raise ValidationError('installId must be 8 to 128 letters, digits, "_" or "-".')
    return text
