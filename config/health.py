"""Liveness and readiness probes."""

from __future__ import annotations

from django.db import connection
from django.http import HttpRequest, HttpResponse, JsonResponse

_LIVENESS_PATH = '/health/live'


class LivenessMiddleware:
    """Answer GET /health/live before host checks, HTTPS redirect, sessions, and the database."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method == 'GET' and request.path.rstrip('/') == _LIVENESS_PATH:
            return HttpResponse('ok', content_type='text/plain')
        return self.get_response(request)


def ready(request: HttpRequest) -> HttpResponse:
    """Readiness: the database accepts a trivial query."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception:
        return JsonResponse({'status': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok'})
