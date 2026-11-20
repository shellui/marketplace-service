"""Prometheus gauges for the public catalog. Counts only, no subjects."""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Gauge, generate_latest

from .models import App, AppInstall, InstallEvent

METRICS_CONTENT_TYPE = CONTENT_TYPE_LATEST


def metrics_http_body() -> bytes:
    registry = CollectorRegistry()
    published = Gauge(
        'shellui_marketplace_apps_published',
        'Published Shellui Marketplace apps.',
        registry=registry,
    )
    active = Gauge(
        'shellui_marketplace_installs_active',
        'Active installs across published apps.',
        registry=registry,
    )
    events = Gauge(
        'shellui_marketplace_install_events',
        'Install and uninstall events.',
        ['action'],
        registry=registry,
    )
    published.set(App.objects.filter(status=App.STATUS_PUBLISHED).count())
    active.set(AppInstall.objects.filter(active=True, app__status=App.STATUS_PUBLISHED).count())
    for action, _label in InstallEvent.ACTION_CHOICES:
        events.labels(action=action).set(InstallEvent.objects.filter(action=action).count())
    return generate_latest(registry)
