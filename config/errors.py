"""HTML error pages for browsers and JSON for /api/ and /metrics."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.template import loader

API_PREFIXES = ('/api/', '/metrics', '/health/')

_JSON = {
    400: 'Bad request.',
    403: 'You do not have permission to perform this action.',
    404: 'Not found.',
    500: 'Server error.',
}

_COPY = {
    400: ("This request didn't work", 'The page got a request it could not read.'),
    403: ("You can't open this page", 'Your account does not have access to this page.'),
    404: ("This page doesn't exist", 'The link may be wrong, or the page has moved.'),
    500: ('Something went wrong', 'The service could not finish your request. Try again in a moment.'),
    'csrf': ('This form has expired', 'Reload the page, then send the form again.'),
}

_FALLBACK_HTML = (
    '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Shellui Marketplace</title></head>'
    '<body><h1>Something went wrong</h1><p>Try again in a moment.</p>'
    '<p><a href="/">Back to home</a></p></body></html>'
)


def is_api_path(request: HttpRequest) -> bool:
    path = request.path or ''
    return path.startswith(API_PREFIXES)


def error_response(request: HttpRequest, status: int, *, csrf: bool = False) -> HttpResponse:
    if is_api_path(request):
        message = 'CSRF check failed. Reload the page and try again.' if csrf else _JSON[status]
        return JsonResponse({'detail': message}, status=status)
    title, message = _COPY['csrf' if csrf else status]
    context = {'status_code': status, 'title': title, 'message': message}
    try:
        body = loader.render_to_string('errors/error.html', context)
    except Exception:  # noqa: BLE001 - an error page must never raise
        body = _FALLBACK_HTML
    return HttpResponse(body, status=status, content_type='text/html; charset=utf-8')


def bad_request(request, exception=None):
    return error_response(request, 400)


def permission_denied(request, exception=None):
    return error_response(request, 403)


def page_not_found(request, exception=None):
    return error_response(request, 404)


def server_error(request):
    return error_response(request, 500)


def csrf_failure(request, reason=''):
    return error_response(request, 403, csrf=True)
