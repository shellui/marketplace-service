"""Shared catalog fixtures and Identity JWTs for tests."""

from __future__ import annotations

import json
import time

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from apps.catalog.models import App, AppScreenshot, AppVersion, Category

ISSUER = 'https://id.test'
AUDIENCE = 'shellui'


def make_category(**overrides) -> Category:
    defaults = {'slug': 'utilities', 'label': 'Utilities', 'position': 1}
    defaults.update(overrides)
    slug = defaults.pop('slug')
    category, _created = Category.objects.get_or_create(slug=slug, defaults=defaults)
    return category


def make_app(*, category: Category | None = None, official: bool = False, **overrides) -> App:
    category = category or make_category()
    navigation = {
        'label': 'Notes',
        'path': '/notes',
        'url': 'https://notes.example/',
        'icon': 'notebook',
    }
    defaults = {
        'slug': 'sample-notes',
        'name': 'Notes',
        'tagline': 'Short notes.',
        'description': 'A sample listing.',
        'category': category,
        'tags': ['notes'],
        'is_official': official,
        'is_verified': not official,
        'publisher_name': 'Shellui' if official else 'Example Studio',
        'publisher_url': 'https://example.com',
        'homepage_url': 'https://example.com/notes',
        'support_url': 'https://example.com/notes/support',
        'icon_url': '/icons/notes.svg',
        'capabilities': ['theme', 'locale', 'ui'],
        'nav_template': navigation,
        'status': App.STATUS_PUBLISHED,
        'baseline_installs': 10,
        'catalog_updated_on': '2026-09-30',
    }
    defaults.update(overrides)
    if 'nav_template' in overrides and overrides['nav_template'] is not None:
        defaults['nav_template'] = overrides['nav_template']
    app = App(**defaults)
    app.full_clean()
    app.save()
    AppVersion.objects.create(app=app, version='0.2.0', changelog='Initial listing.')
    AppScreenshot.objects.create(app=app, src='/previews/notes-page.svg', alt='Notes preview', position=0)
    return app


def identity_token(sub: str = 'user-1', *, jti: str | None = None):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(RSAAlgorithm.to_jwk(key.public_key()))
    jwk.update({'kid': 'test-key', 'alg': 'RS256', 'use': 'sig'})
    now = int(time.time())
    token = jwt.encode(
        {
            'sub': sub,
            'scope': 'openid',
            'jti': jti or f'jti-{sub}',
            'iat': now,
            'exp': now + 600,
            'iss': ISSUER,
            'aud': AUDIENCE,
        },
        key,
        algorithm='RS256',
        headers={'kid': 'test-key'},
    )
    return token, {'keys': [jwk]}
