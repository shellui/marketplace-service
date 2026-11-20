"""Optional Bearer tokens checked with shellui-django Identity JWKS helpers."""

from __future__ import annotations

from django.conf import settings
from rest_framework import authentication, exceptions
from shellui_django.mcp.identity_jwks import IdentityJwksError, decode_identity_rs256_jwt


class IdentityPrincipal:
    """Signed-in subject from an Identity JWT. Only the `sub` claim is kept in memory."""

    def __init__(self, sub: str):
        self.sub = sub
        self.is_authenticated = True
        self.is_staff = False
        self.is_anonymous = False

    def __str__(self) -> str:
        return 'identity-user'


class OptionalIdentityAuthentication(authentication.BaseAuthentication):
    """Verify a Bearer token when present. A missing header stays anonymous.

    Invalid tokens are rejected. They are never treated as anonymous, so a broken
    signature cannot fall through and share another person's install row.
    """

    keyword = 'Bearer'

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode('utf-8')
        if not header:
            return None
        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            raise exceptions.AuthenticationFailed('Invalid Authorization header.')
        raw_token = parts[1]
        issuer = settings.IDENTITY_ISSUER
        audience = settings.IDENTITY_AUDIENCE
        if not issuer or not audience or (not settings.IDENTITY_JWKS_DOCUMENT and not settings.IDENTITY_JWKS_URL):
            raise exceptions.AuthenticationFailed(
                'Token is invalid or could not be verified against identity JWKS.'
            )
        try:
            claims = decode_identity_rs256_jwt(
                raw_token,
                audience=audience,
                issuer=issuer,
                jwks_url=None if settings.IDENTITY_JWKS_DOCUMENT else settings.IDENTITY_JWKS_URL,
                jwks=settings.IDENTITY_JWKS_DOCUMENT,
            )
        except IdentityJwksError as exc:
            raise exceptions.AuthenticationFailed(
                'Token is invalid or could not be verified against identity JWKS.'
            ) from exc
        sub = claims.get('sub')
        if not isinstance(sub, str) or not sub.strip():
            raise exceptions.AuthenticationFailed(
                'Token is invalid or could not be verified against identity JWKS.'
            )
        return (IdentityPrincipal(sub.strip()), None)

    def authenticate_header(self, request):
        return self.keyword
