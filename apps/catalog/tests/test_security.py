"""Mitigations from SECURITY.md: catalog poisoning, nav templates, stats spam, and PII."""

import json

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.catalog.models import App, AppInstall, InstallEvent
from apps.catalog.tests.helpers import AUDIENCE, ISSUER, identity_token, make_app


def _blob():
    rows = []
    for model in (AppInstall, InstallEvent):
        for row in model.objects.values():
            rows.append(json.dumps(row, default=str))
    return '\n'.join(rows)


class CatalogPoisoningTests(TestCase):
    def test_poisoned_navigation_url_is_withheld(self):
        app = make_app()
        App.objects.filter(pk=app.pk).update(
            nav_template={
                'label': 'Notes',
                'path': '/notes',
                'url': 'javascript:alert(1)',
                'icon': 'notebook',
            }
        )
        self.assertEqual(self.client.get(f'/api/apps/{app.slug}').status_code, 404)
        slugs = [item['slug'] for item in self.client.get('/api/apps').json()['apps']]
        self.assertNotIn(app.slug, slugs)

    def test_third_party_auth_flag_is_not_published(self):
        app = make_app()
        App.objects.filter(pk=app.pk).update(
            capabilities=['theme', 'auth'],
            nav_template={
                'label': 'Notes',
                'path': '/notes',
                'url': 'https://notes.example/',
                'icon': 'notebook',
                'safeForAuthToken': True,
            },
        )
        self.assertEqual(self.client.get(f'/api/apps/{app.slug}').status_code, 404)

    def test_admin_form_rejects_auth_on_a_third_party_app(self):
        user = get_user_model().objects.create_superuser('curator', 'curator@example.com', 'not-a-real-password')
        self.client.force_login(user)
        app = make_app()
        add = self.client.get('/admin/catalog/app/add/')
        self.assertEqual(add.status_code, 200)
        self.assertContains(add, 'Shellui Marketplace')
        app.capabilities = ['theme', 'auth']
        with self.assertRaises(ValidationError):
            app.full_clean()
        analytics = self.client.get('/admin/analytics/')
        self.assertEqual(analytics.status_code, 200)
        self.assertContains(analytics, 'Install analytics')
        self.assertContains(analytics, app.name)


_TIGHT_THROTTLE = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_THROTTLE_RATES': {'install': '2/min'},
    'EXCEPTION_HANDLER': 'apps.catalog.exceptions.exception_handler',
}


class StatsSpamAndPiiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.app = make_app()
        self.client = APIClient(enforce_csrf_checks=True)
        self.url = f'/api/apps/{self.app.slug}/install'

    def test_content_type_origin_and_extra_fields(self):
        bad_type = self.client.post(self.url, data='{}', content_type='text/plain')
        self.assertEqual(bad_type.status_code, 415)
        leaked = self.client.post(
            self.url,
            {'installId': 'abcdefgh', 'email': 'person@example.com'},
            format='json',
            HTTP_ORIGIN='https://market.example',
        )
        self.assertEqual(leaked.status_code, 400)
        self.assertEqual(AppInstall.objects.count(), 0)
        bad_origin = self.client.post(
            self.url,
            {'installId': 'abcdefgh'},
            format='json',
            HTTP_ORIGIN='https://market.example/app',
        )
        self.assertEqual(bad_origin.status_code, 400)
        self.assertEqual(bad_origin.json()['detail'], 'invalid_origin')

    def test_anonymous_pings_dedupe_and_do_not_store_pii(self):
        origin = 'https://Market.Example'
        install_id = 'anon-install-1'
        first = self.client.post(self.url, {'installId': install_id}, format='json', HTTP_ORIGIN=origin)
        second = self.client.post(self.url, {'installId': install_id}, format='json', HTTP_ORIGIN=origin)
        other = self.client.post(
            self.url,
            {'installId': 'anon-install-2'},
            format='json',
            HTTP_ORIGIN=origin,
        )
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.json()['counted'])
        self.assertEqual(first.json()['installCount'], 11)
        self.assertEqual(second.json()['installCount'], 11)
        self.assertEqual(InstallEvent.objects.filter(action='install').count(), 2)
        self.assertEqual(other.json()['installCount'], 12)
        stored = _blob()
        self.assertNotIn(install_id, stored)
        self.assertNotIn('market.example', stored.lower())
        self.assertNotIn('127.0.0.1', stored)
        empty = self.client.post(self.url, {}, format='json', HTTP_ORIGIN=origin)
        self.assertFalse(empty.json()['counted'])
        self.assertEqual(empty.json()['reason'], 'dedupe_key_required')

    @override_settings(REST_FRAMEWORK=_TIGHT_THROTTLE)
    def test_rate_limit_per_ip_hash(self):
        for _ in range(2):
            response = self.client.post(self.url, {}, format='json', HTTP_ORIGIN='https://market.example')
            self.assertEqual(response.status_code, 200)
        blocked = self.client.post(self.url, {}, format='json', HTTP_ORIGIN='https://market.example')
        self.assertEqual(blocked.status_code, 429)
        self.assertNotIn('127.0.0.1', blocked.content.decode())

    def test_signed_in_installs_dedupe_on_the_subject_hash(self):
        token, jwks = identity_token('user-sub-42')
        other_token, other_jwks = identity_token('user-sub-99')
        with override_settings(IDENTITY_JWKS_DOCUMENT=jwks, IDENTITY_ISSUER=ISSUER, IDENTITY_AUDIENCE=AUDIENCE):
            first = self.client.post(self.url, {}, format='json', HTTP_AUTHORIZATION=f'Bearer {token}')
            again = self.client.post(self.url, {}, format='json', HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(again.json()['installCount'], first.json()['installCount'])
        self.assertEqual(AppInstall.objects.count(), 1)
        self.assertNotIn('user-sub-42', _blob())
        with override_settings(
            IDENTITY_JWKS_DOCUMENT=other_jwks,
            IDENTITY_ISSUER=ISSUER,
            IDENTITY_AUDIENCE=AUDIENCE,
        ):
            other = self.client.post(
                self.url,
                {},
                format='json',
                HTTP_AUTHORIZATION=f'Bearer {other_token}',
            )
        self.assertEqual(other.json()['installCount'], 12)
        removed = self.client.post(
            f'/api/apps/{self.app.slug}/uninstall',
            {'installId': 'anon-install-9'},
            format='json',
            HTTP_ORIGIN='https://market.example',
        )
        self.assertEqual(removed.status_code, 200)
        self.assertFalse(removed.json()['active'])

    def test_invalid_bearer_is_rejected(self):
        response = self.client.post(self.url, {}, format='json', HTTP_AUTHORIZATION='Bearer not-a-jwt')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(AppInstall.objects.count(), 0)

    def test_uninstall_is_idempotent(self):
        origin = 'https://market.example'
        body = {'installId': 'anon-install-1'}
        self.client.post(self.url, body, format='json', HTTP_ORIGIN=origin)
        first = self.client.post(
            f'/api/apps/{self.app.slug}/uninstall',
            body,
            format='json',
            HTTP_ORIGIN=origin,
        )
        second = self.client.post(
            f'/api/apps/{self.app.slug}/uninstall',
            body,
            format='json',
            HTTP_ORIGIN=origin,
        )
        self.assertFalse(first.json()['active'])
        self.assertEqual(first.json()['installCount'], 10)
        self.assertEqual(InstallEvent.objects.filter(action='uninstall').count(), 1)
        self.assertEqual(second.json()['installCount'], 10)
        self.assertFalse(AppInstall.objects.get().active)
