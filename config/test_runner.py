"""Test runner that keeps media writes off the real filesystem and S3 bucket."""

from __future__ import annotations

import tempfile
from pathlib import Path

from django.conf import settings
from django.test.runner import DiscoverRunner
from django.test.utils import override_settings


class IsolatedMediaDiscoverRunner(DiscoverRunner):
    """Force a local FileSystemStorage in a temp dir for the whole suite."""

    def setup_test_environment(self, **kwargs):
        self._media_tmpdir = tempfile.TemporaryDirectory(prefix='shellui-marketplace-tests-')
        media_root = Path(self._media_tmpdir.name)
        self._media_override = override_settings(
            STORAGE_BACKEND='filesystem',
            MEDIA_ROOT=str(media_root),
            TEST_MODE=True,
            CATALOG_CACHE_SECONDS=0,
            AWS_STORAGE_BUCKET_NAME='',
            AWS_ACCESS_KEY_ID='',
            AWS_SECRET_ACCESS_KEY='',
            AWS_S3_ENDPOINT_URL=None,
            STORAGES={
                'default': {
                    'BACKEND': 'django.core.files.storage.FileSystemStorage',
                    'OPTIONS': {
                        'location': str(media_root),
                        'base_url': settings.MEDIA_URL,
                    },
                },
                'staticfiles': settings.STORAGES['staticfiles'],
            },
        )
        self._media_override.enable()
        super().setup_test_environment(**kwargs)

    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)
        self._media_override.disable()
        self._media_tmpdir.cleanup()
