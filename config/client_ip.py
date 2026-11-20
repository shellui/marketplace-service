"""Client address for rate-limit keys. Callers hash the result and do not store it."""

from __future__ import annotations

from django.conf import settings


def client_ip(request) -> str:
    """Return the client address used only as a rate-limit input.

    Honor the first X-Forwarded-For hop when TRUST_PROXY is set (Coolify and other
    reverse proxies). Otherwise use REMOTE_ADDR. Never log the return value.
    """
    remote = (request.META.get('REMOTE_ADDR') or '').strip() or 'unknown'
    if not getattr(settings, 'TRUST_PROXY', False):
        return remote
    forwarded = (request.META.get('HTTP_X_FORWARDED_FOR') or '').split(',')[0].strip()
    return forwarded or remote
