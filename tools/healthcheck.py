#!/usr/bin/env python3
"""Container health check: GET /health/live on the local gunicorn port.

/health/live answers in LivenessMiddleware, before SecurityMiddleware, sessions,
and the database. It needs no auth and is not redirected to https.
"""

import os
import sys
import urllib.request


def main() -> int:
    hosts = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '').split(',') if h.strip()]
    host = next((h.lstrip('.') for h in hosts if h != '*'), 'localhost')
    request = urllib.request.Request(
        'http://127.0.0.1:8000/health/live',
        headers={'Host': host, 'X-Forwarded-Proto': 'https'},
    )
    try:
        with urllib.request.urlopen(request, timeout=4) as response:
            return 0 if response.status == 200 else 1
    except Exception as exc:  # noqa: BLE001
        print(f'healthcheck failed: {type(exc).__name__}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
