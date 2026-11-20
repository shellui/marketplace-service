"""Install and uninstall records. Stores a subject hash, never an address or user id."""

from __future__ import annotations

import logging

from django.db import IntegrityError, transaction

from .models import App, AppInstall, InstallEvent

logger = logging.getLogger(__name__)


def record_install(*, app: App, subject_hash: str, kind: str) -> bool:
    """Mark an install active. Returns True when this call changed state."""
    with transaction.atomic():
        try:
            install, created = AppInstall.objects.select_for_update().get_or_create(
                app=app,
                subject_hash=subject_hash,
                defaults={'kind': kind, 'active': True},
            )
        except IntegrityError:
            install = AppInstall.objects.select_for_update().get(app=app, subject_hash=subject_hash)
            created = False
        if created:
            InstallEvent.objects.create(
                app=app,
                action=InstallEvent.ACTION_INSTALL,
                subject_hash=subject_hash,
            )
            logger.info('install recorded app=%s kind=%s', app.slug, kind)
            return True
        if install.active:
            return False
        install.active = True
        install.kind = kind
        install.save(update_fields=['active', 'kind', 'updated_at'])
        InstallEvent.objects.create(
            app=app,
            action=InstallEvent.ACTION_INSTALL,
            subject_hash=subject_hash,
        )
        logger.info('install recorded app=%s kind=%s', app.slug, kind)
        return True


def record_uninstall(*, app: App, subject_hash: str) -> bool:
    """Mark an install inactive. Returns True when this call changed state."""
    with transaction.atomic():
        try:
            install = AppInstall.objects.select_for_update().get(app=app, subject_hash=subject_hash)
        except AppInstall.DoesNotExist:
            return False
        if not install.active:
            return False
        install.active = False
        install.save(update_fields=['active', 'updated_at'])
        InstallEvent.objects.create(
            app=app,
            action=InstallEvent.ACTION_UNINSTALL,
            subject_hash=subject_hash,
        )
        logger.info('uninstall recorded app=%s', app.slug)
        return True
