"""Print a Coolify-friendly env file. Runs without Django settings."""

from __future__ import annotations

import argparse
import secrets
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Print Shellui Marketplace environment variables.')
    parser.add_argument('--host', required=True, help='Public host, without a scheme (market.example.com).')
    parser.add_argument(
        '--identity',
        default='https://id.example.com',
        help='identity-service origin.',
    )
    args = parser.parse_args(argv)
    host = args.host.strip().rstrip('/')
    if '://' in host or not host:
        print('Pass a host name without a scheme.', file=sys.stderr)
        return 2
    identity = args.identity.strip().rstrip('/')
    secret = secrets.token_urlsafe(64)
    print(
        '\n'.join(
            [
                f'SECRET_KEY={secret}',
                'DEBUG=false',
                f'ALLOWED_HOSTS={host}',
                f'CSRF_TRUSTED_ORIGINS=https://{host}',
                'POSTGRES_DATABASE_URL=postgres://marketplace:marketplace@postgres:5432/marketplace',
                'POSTGRES_SSL_REQUIRE=true',
                'REDIS_URL=redis://redis:6379/0',
                'STORAGE_BACKEND=filesystem',
                f'IDENTITY_SERVICE_URL={identity}',
                f'IDENTITY_ISSUER={identity}',
                'IDENTITY_AUDIENCE=shellui',
                'CORS_ALLOW_ALL_ORIGINS=true',
                'TRUST_PROXY=true',
                'SECURE_SSL_REDIRECT=true',
                'SENTRY_DSN=',
            ]
        )
    )
    return 0
