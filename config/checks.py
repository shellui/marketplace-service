"""Deploy checks. They run with `manage.py check --deploy`, not during the test suite."""

from django.conf import settings
from django.core.checks import Error, register

SECRET_KEY_MIN_LENGTH = 50


@register(deploy=True)
def production_settings(app_configs, **kwargs):
    if settings.DEBUG:
        return []
    errors = []
    key = (settings.SECRET_KEY or '').strip()
    if len(key) < SECRET_KEY_MIN_LENGTH:
        errors.append(
            Error(
                f'SECRET_KEY must be at least {SECRET_KEY_MIN_LENGTH} characters when DEBUG is false.',
                id='marketplace.E001',
            )
        )
    if not (settings.REDIS_URL or '').strip():
        errors.append(
            Error(
                'REDIS_URL is required when DEBUG is false so install rate limits are shared across workers.',
                hint='Example: redis://redis:6379/0',
                id='marketplace.E002',
            )
        )
    hosts = [host for host in settings.ALLOWED_HOSTS if host and host != '*']
    if not hosts:
        errors.append(
            Error(
                'ALLOWED_HOSTS must name the public host when DEBUG is false.',
                id='marketplace.E003',
            )
        )
    if not settings.IDENTITY_ISSUER or not settings.IDENTITY_AUDIENCE:
        errors.append(
            Error(
                'IDENTITY_ISSUER and IDENTITY_AUDIENCE are required when DEBUG is false.',
                hint='Match the JWT issuer and audience configured on identity-service.',
                id='marketplace.E004',
            )
        )
    if not settings.IDENTITY_JWKS_DOCUMENT and not settings.IDENTITY_JWKS_URL:
        errors.append(
            Error(
                'Set IDENTITY_JWKS, IDENTITY_JWKS_FILE, or IDENTITY_JWKS_URL so install tokens can be verified.',
                id='marketplace.E005',
            )
        )
    return errors
