from django.http import HttpResponse
from django.urls import path

from .metrics import METRICS_CONTENT_TYPE, metrics_http_body


def metrics_view(request):
    if request.method != 'GET':
        return HttpResponse(status=405)
    return HttpResponse(metrics_http_body(), content_type=METRICS_CONTENT_TYPE)


urlpatterns = [
    path('metrics', metrics_view, name='metrics'),
]
