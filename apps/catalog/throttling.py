"""Per-IP install throttle. The cache key is a hash. The address is not stored or logged."""

from __future__ import annotations

import hashlib

from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle

from config.client_ip import client_ip


class InstallRateThrottle(SimpleRateThrottle):
    scope = 'install'

    def get_rate(self):
        # Read the live setting so tests can override INSTALL rates.
        rates = settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES', {})
        return rates.get(self.scope)

    def get_cache_key(self, request, view):
        digest = hashlib.sha256(client_ip(request).encode('utf-8')).hexdigest()
        return self.cache_format % {'scope': self.scope, 'ident': digest}
