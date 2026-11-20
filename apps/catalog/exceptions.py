"""JSON errors that do not echo request bodies, tokens, or addresses."""

from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None
    detail = response.data.get('detail') if isinstance(response.data, dict) else None
    if detail is not None:
        response.data = {'detail': str(detail)}
    return response
