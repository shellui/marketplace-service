from django.core.management import call_command
from django.test import TestCase

from apps.catalog.models import App
from apps.catalog.seed import SEED_APPS
from apps.catalog.tests.helpers import make_app, make_category


class CatalogApiTests(TestCase):
    def test_seed_matches_the_directory_fallback(self):
        call_command('seed_marketplace')
        call_command('seed_marketplace')
        response = self.client.get('/api/apps')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['count'], len(SEED_APPS))
        by_slug = {app['slug']: app for app in payload['apps']}
        files = by_slug['files']
        self.assertEqual(files['name'], 'Files')
        self.assertEqual(files['tagline'], 'Folders, upload, and share links for storage-service.')
        self.assertEqual(files['publisher']['kind'], 'official')
        self.assertEqual(files['publisher']['name'], 'Shellui')
        self.assertEqual(files['installCount'], 1840)
        self.assertEqual(files['updatedAt'], '2026-11-02')
        self.assertEqual(files['navigation']['path'], '/files')
        self.assertEqual(files['navigation']['url'], 'https://files.shellui.com/')
        self.assertEqual(files['capabilities'], ['theme', 'locale', 'ui', 'navigate', 'storage'])
        self.assertTrue(files['official'])
        self.assertFalse(files['safeForAuthToken'])
        self.assertEqual(files['url'], 'https://files.shellui.com/')
        self.assertEqual(files['path'], '/files')
        notes = by_slug['notes']
        self.assertEqual(notes['publisher']['kind'], 'verified')
        self.assertFalse(notes['official'])
        categories = self.client.get('/api/categories').json()['categories']
        self.assertIn({'id': 'productivity', 'label': 'Productivity'}, categories)
        detail = self.client.get('/api/apps/files').json()['app']
        self.assertEqual(detail['slug'], 'files')
        self.assertEqual(detail['screenshots'][0]['alt'], 'Files preview: a folder list')

    def test_filters_sort_and_pagination(self):
        call_command('seed_marketplace')
        official = self.client.get('/api/apps?official=true&sort=name')
        names = [app['name'] for app in official.json()['apps']]
        self.assertEqual(names, sorted(names))
        self.assertTrue(all(app['official'] for app in official.json()['apps']))
        community = self.client.get('/api/apps?official=false')
        self.assertEqual(
            sorted(app['slug'] for app in community.json()['apps']),
            ['notes', 'status-board'],
        )
        docs = self.client.get('/api/apps?category=documentation')
        self.assertEqual([app['slug'] for app in docs.json()['apps']], ['docs'])
        search = self.client.get('/api/apps?q=status')
        self.assertEqual([app['slug'] for app in search.json()['apps']], ['status-board'])
        recent = self.client.get('/api/apps?sort=recent')
        self.assertEqual(recent.json()['apps'][0]['slug'], 'docs')
        page = self.client.get('/api/apps?sort=name&page=2&page_size=2')
        body = page.json()
        self.assertEqual(body['count'], 7)
        self.assertEqual(body['page'], 2)
        self.assertEqual(len(body['apps']), 2)
        self.assertEqual(self.client.get('/api/apps?sort=nope').status_code, 400)

    def test_unlisted_apps_stay_out_of_the_catalog(self):
        app = make_app()
        app.status = App.STATUS_UNLISTED
        app.save(update_fields=['status'])
        slugs = [item['slug'] for item in self.client.get('/api/apps').json()['apps']]
        self.assertNotIn(app.slug, slugs)
        self.assertEqual(self.client.get(f'/api/apps/{app.slug}').status_code, 404)

    def test_slash_slug_and_encoded_slash(self):
        category = make_category(slug='productivity', label='Productivity')
        make_app(category=category, slug='shellui/files', name='Files')
        plain = self.client.get('/api/apps/shellui/files')
        encoded = self.client.get('/api/apps/shellui%2Ffiles')
        self.assertEqual(plain.status_code, 200)
        self.assertEqual(encoded.status_code, 200)
        self.assertEqual(plain.json()['app']['slug'], 'shellui/files')
        self.assertEqual(encoded.json()['app']['slug'], 'shellui/files')

    def test_openapi_lists_the_catalog(self):
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn('/api/apps', body)
        self.assertIn('/api/categories', body)
        self.assertIn('Shellui Marketplace', body)

    def test_cors_is_open_for_catalog_gets(self):
        response = self.client.get('/api/apps', HTTP_ORIGIN='https://market.example')
        self.assertEqual(response['Access-Control-Allow-Origin'], '*')

    def test_health_and_metrics(self):
        self.assertEqual(self.client.get('/health/live').content, b'ok')
        self.assertEqual(self.client.get('/health/ready').json()['status'], 'ok')
        metrics = self.client.get('/metrics')
        self.assertEqual(metrics.status_code, 200)
        self.assertIn(b'shellui_marketplace_apps_published', metrics.content)
        home = self.client.get('/')
        self.assertContains(home, 'Shellui Marketplace')
