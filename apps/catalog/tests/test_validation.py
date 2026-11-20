from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from apps.catalog.models import App
from apps.catalog.tests.helpers import make_app, make_category
from apps.catalog.validation import validate_absolute_url, validate_nav_template, validate_origin


class UrlValidationTests(TestCase):
    def test_https_is_kept(self):
        self.assertEqual(validate_absolute_url('https://files.shellui.com/'), 'https://files.shellui.com/')

    def test_http_and_javascript_are_rejected(self):
        with self.assertRaises(ValidationError):
            validate_absolute_url('http://notes.example/')
        with self.assertRaises(ValidationError):
            validate_absolute_url('javascript:alert(1)')

    @override_settings(DEBUG=True)
    def test_localhost_http_is_allowed_in_debug(self):
        self.assertEqual(
            validate_absolute_url('http://localhost:5173/app'),
            'http://localhost:5173/app',
        )

    def test_localhost_http_is_rejected_outside_debug(self):
        with self.assertRaises(ValidationError):
            validate_absolute_url('http://127.0.0.1:8000/')


class CapabilityValidationTests(TestCase):
    def test_third_party_cannot_request_auth(self):
        app = make_app()
        app.capabilities = ['theme', 'auth']
        with self.assertRaises(ValidationError):
            app.full_clean()

    def test_official_app_can_request_auth(self):
        app = make_app(official=True, slug='official-admin', name='Admin')
        app.capabilities = ['theme', 'ui', 'auth']
        app.nav_template = {
            'label': 'Admin',
            'path': '/admin',
            'url': 'https://admin.shellui.com/',
            'icon': 'shield',
            'safeForAuthToken': True,
        }
        app.full_clean()

    def test_nav_template_rejects_extra_keys_and_traversal(self):
        with self.assertRaises(ValidationError):
            validate_nav_template(
                {
                    'label': 'Notes',
                    'path': '/notes',
                    'url': 'https://notes.example/',
                    'icon': 'notebook',
                    'html': '<script>',
                },
                official=False,
            )
        with self.assertRaises(ValidationError):
            validate_nav_template(
                {
                    'label': 'Notes',
                    'path': '/../admin',
                    'url': 'https://notes.example/',
                    'icon': 'notebook',
                },
                official=False,
            )

    def test_origin_format(self):
        self.assertEqual(validate_origin('https://market.example'), 'https://market.example')
        with self.assertRaises(ValidationError):
            validate_origin('https://market.example/app')
        with self.assertRaises(ValidationError):
            validate_origin('null')
        with self.assertRaises(ValidationError):
            validate_origin('http://market.example')


class ModelSaveTests(TestCase):
    def test_slug_with_one_slash_is_valid(self):
        category = make_category(slug='productivity', label='Productivity')
        app = make_app(category=category, slug='shellui/files', name='Files')
        self.assertEqual(App.objects.get(slug='shellui/files').name, app.name)
