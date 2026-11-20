"""Published catalog queries, counts, and trending scores."""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db.models import Count, F, Q
from django.utils import timezone

from .models import App, InstallEvent


def published_apps():
    return (
        App.objects.filter(status=App.STATUS_PUBLISHED)
        .select_related('category')
        .prefetch_related('screenshots', 'versions')
        .annotate(
            active_installs=Count('installs', filter=Q(installs__active=True), distinct=True),
        )
        .annotate(install_total=F('baseline_installs') + F('active_installs'))
    )


def trending_scores() -> dict[int, int]:
    since = timezone.now() - timedelta(days=settings.TRENDING_WINDOW_DAYS)
    rows = (
        InstallEvent.objects.filter(action=InstallEvent.ACTION_INSTALL, created_at__gte=since)
        .values('app_id')
        .annotate(score=Count('id'))
    )
    return {row['app_id']: row['score'] for row in rows}


def trending_ids(scores: dict[int, int]) -> set[int]:
    ranked = sorted((score, app_id) for app_id, score in scores.items() if score > 0)
    ranked.sort(reverse=True)
    return {app_id for _, app_id in ranked[:3]}
