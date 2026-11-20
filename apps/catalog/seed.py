"""Directory seed shared by the data migration and `seed_marketplace`.

The rows match the fallback catalog in shellui/marketplace (`src/lib/catalog.ts`)
so the directory and this service list the same apps.
"""

from __future__ import annotations

from datetime import date

SEED_CATEGORIES = [
    {'id': 'productivity', 'label': 'Productivity'},
    {'id': 'administration', 'label': 'Administration'},
    {'id': 'documentation', 'label': 'Documentation'},
    {'id': 'ai', 'label': 'AI'},
    {'id': 'utilities', 'label': 'Utilities'},
]

_SHELL = {'name': 'Shellui', 'kind': 'official', 'url': 'https://shellui.com'}

SEED_APPS = [
    {
        'slug': 'files',
        'name': 'Files',
        'tagline': 'Folders, upload, and share links for storage-service.',
        'description': (
            'Browse a company file tree, upload, download, move, and rename. '
            'Share links and access grants stay on storage-service. File calls go through @shellui/sdk, '
            'so the app does not keep a storage URL of its own.'
        ),
        'publisher': _SHELL,
        'category': 'productivity',
        'version': '0.3.0',
        'homepage': 'https://files.shellui.com/',
        'support': 'https://github.com/shellui/files/issues',
        'icon': '/icons/files.svg',
        'screenshots': [
            {'src': '/previews/files-list.svg', 'alt': 'Files preview: a folder list'},
            {'src': '/previews/files-share.svg', 'alt': 'Files preview: a share link'},
        ],
        'installCount': 1840,
        'updatedAt': '2026-11-02',
        'featured': True,
        'capabilities': ['theme', 'locale', 'ui', 'navigate', 'storage'],
        'navigation': {
            'label': 'Files',
            'path': '/files',
            'url': 'https://files.shellui.com/',
            'icon': 'folder',
        },
        'changelog': 'Directory seed for the Files app.',
    },
    {
        'slug': 'admin',
        'name': 'Admin',
        'tagline': 'People, groups, sign-in, and the services on the shell.',
        'description': (
            'Company owners and staff run the workspace from Admin: users, groups, sign-in methods, '
            'OAuth apps, SCIM, and webhooks. Storage, Hosting, and Email sections appear when '
            'shellui.config.json names those services. The shell loads Admin at /admin.'
        ),
        'publisher': _SHELL,
        'category': 'administration',
        'version': '0.10.0',
        'homepage': 'https://admin.shellui.com/',
        'support': 'https://github.com/shellui/admin/issues',
        'icon': '/icons/admin.svg',
        'screenshots': [
            {'src': '/previews/admin-users.svg', 'alt': 'Admin preview: people and groups'},
            {'src': '/previews/admin-signin.svg', 'alt': 'Admin preview: sign-in methods'},
        ],
        'installCount': 1620,
        'updatedAt': '2026-10-28',
        'featured': True,
        'capabilities': ['theme', 'locale', 'ui', 'navigate', 'storage'],
        'navigation': {
            'label': 'Admin',
            'path': '/admin',
            'url': 'https://admin.shellui.com/',
            'icon': 'shield',
        },
        'changelog': 'Directory seed for the Admin app.',
    },
    {
        'slug': 'dashboard',
        'name': 'Dashboard',
        'tagline': 'The shell home: session, navigation, and configured apps.',
        'description': (
            'Dashboard is the shell you open in the browser. It shows the signed-in session and the '
            'navigation from shellui.config.json. Add other apps beside it. Point the snippet url at '
            'your shell origin.'
        ),
        'publisher': _SHELL,
        'category': 'administration',
        'version': '0.8.1',
        'homepage': 'https://dashboard.shellui.com/',
        'support': 'https://github.com/shellui/shellui/issues',
        'icon': '/icons/dashboard.svg',
        'screenshots': [
            {'src': '/previews/dashboard-home.svg', 'alt': 'Dashboard preview: the shell home'},
            {'src': '/previews/dashboard-nav.svg', 'alt': 'Dashboard preview: navigation'},
        ],
        'installCount': 2104,
        'updatedAt': '2026-10-18',
        'featured': True,
        'capabilities': ['theme', 'locale', 'ui', 'navigate'],
        'navigation': {
            'label': 'Dashboard',
            'path': '/dashboard',
            'url': 'https://dashboard.shellui.com/',
            'icon': 'layout-dashboard',
        },
        'changelog': 'Directory seed for the Dashboard app.',
    },
    {
        'slug': 'assistant',
        'name': 'AI Assistant',
        'tagline': 'On-device models through the shell AI client.',
        'description': (
            'Ask the model the shell runs on the device. Calls use shellui.ai. The shell answers '
            'unavailable until you turn AI on under Settings, then AI, and a model is ready. The public '
            'notes for that surface live with the Shellui docs.'
        ),
        'publisher': _SHELL,
        'category': 'ai',
        'version': '0.8.1',
        'homepage': 'https://docs.shellui.com/features/ai-native/',
        'support': 'https://github.com/shellui/shellui/issues',
        'icon': '/icons/assistant.svg',
        'screenshots': [
            {'src': '/previews/assistant-chat.svg', 'alt': 'AI Assistant preview: a prompt'},
            {'src': '/previews/assistant-models.svg', 'alt': 'AI Assistant preview: the model list'},
        ],
        'installCount': 640,
        'updatedAt': '2026-10-20',
        'featured': True,
        'capabilities': ['theme', 'locale', 'ui', 'navigate', 'ai'],
        'navigation': {
            'label': 'AI Assistant',
            'path': '/assistant',
            'url': 'https://docs.shellui.com/features/ai-native/',
            'icon': 'sparkles',
        },
        'changelog': 'Directory seed for the AI Assistant app.',
    },
    {
        'slug': 'docs',
        'name': 'Docs',
        'tagline': 'Shell, SDK, identity, storage, and administration.',
        'description': (
            'Read the Shellui docs in the shell: navigation, themes, storage, administration, and the SDK. '
            'The same pages are on docs.shellui.com.'
        ),
        'publisher': _SHELL,
        'category': 'documentation',
        'version': '0.8.1',
        'homepage': 'https://docs.shellui.com/',
        'support': 'https://github.com/shellui/website/issues',
        'icon': '/icons/docs.svg',
        'screenshots': [
            {'src': '/previews/docs-guide.svg', 'alt': 'Docs preview: a guide'},
            {'src': '/previews/docs-sdk.svg', 'alt': 'Docs preview: the SDK reference'},
        ],
        'installCount': 3012,
        'updatedAt': '2026-11-12',
        'featured': True,
        'capabilities': ['theme', 'locale', 'ui', 'navigate'],
        'navigation': {
            'label': 'Docs',
            'path': '/docs',
            'url': 'https://docs.shellui.com/',
            'icon': 'book-open',
        },
        'changelog': 'Directory seed for the Docs app.',
    },
    {
        'slug': 'notes',
        'name': 'Notes',
        'tagline': 'Sample community app that keeps short notes in storage.',
        'description': (
            'Notes is sample catalog data so the directory has a verified third-party listing when '
            'marketplace-service is offline. It is not a published Shellui app. The sample asks for '
            'storage so it can keep notes beside your files.'
        ),
        'publisher': {'name': 'Example Studio', 'kind': 'verified', 'url': 'https://example.com'},
        'category': 'productivity',
        'version': '0.2.0',
        'homepage': 'https://example.com/notes',
        'support': 'https://example.com/notes/support',
        'icon': '/icons/notes.svg',
        'screenshots': [
            {'src': '/previews/notes-page.svg', 'alt': 'Notes preview: a note list'},
            {'src': '/previews/notes-edit.svg', 'alt': 'Notes preview: an editor'},
        ],
        'installCount': 428,
        'updatedAt': '2026-09-30',
        'featured': False,
        'capabilities': ['theme', 'locale', 'ui', 'storage'],
        'navigation': {
            'label': 'Notes',
            'path': '/notes',
            'url': 'https://notes.example.com/',
            'icon': 'notebook',
        },
        'changelog': 'Sample community listing. Not a Shellui app.',
    },
    {
        'slug': 'status-board',
        'name': 'Status Board',
        'tagline': 'Sample community app that lists service checks.',
        'description': (
            'Status Board is sample catalog data for a community listing. It is not a published Shellui app. '
            'The sample shows how a third-party publisher and a utilities category appear in the directory.'
        ),
        'publisher': {'name': 'Example Collective', 'kind': 'community', 'url': 'https://example.com'},
        'category': 'utilities',
        'version': '0.1.0',
        'homepage': 'https://example.com/status',
        'support': 'https://example.com/status/support',
        'icon': '/icons/status.svg',
        'screenshots': [
            {'src': '/previews/status-board.svg', 'alt': 'Status Board preview: a list of checks'},
            {'src': '/previews/status-detail.svg', 'alt': 'Status Board preview: one check'},
        ],
        'installCount': 196,
        'updatedAt': '2026-08-14',
        'featured': False,
        'capabilities': ['theme', 'locale', 'ui', 'navigate'],
        'navigation': {
            'label': 'Status Board',
            'path': '/status',
            'url': 'https://status.example.com/',
            'icon': 'activity',
        },
        'changelog': 'Sample community listing. Not a Shellui app.',
    },
]


def seed_marketplace(apps=None) -> tuple[int, int]:
    """Create or update the directory seed. Returns (created, updated) app counts."""
    if apps is None:
        from django.apps import apps as django_apps

        apps = django_apps
    category_model = apps.get_model('catalog', 'Category')
    app_model = apps.get_model('catalog', 'App')
    version_model = apps.get_model('catalog', 'AppVersion')
    screenshot_model = apps.get_model('catalog', 'AppScreenshot')

    categories = {}
    for position, item in enumerate(SEED_CATEGORIES):
        category, _created = category_model.objects.update_or_create(
            slug=item['id'],
            defaults={'label': item['label'], 'position': position},
        )
        categories[item['id']] = category

    created = 0
    updated = 0
    for item in SEED_APPS:
        publisher = item['publisher']
        defaults = {
            'name': item['name'],
            'tagline': item['tagline'],
            'description': item['description'],
            'category': categories[item['category']],
            'tags': [],
            'is_official': publisher['kind'] == 'official',
            'is_verified': publisher['kind'] == 'verified',
            'featured': item['featured'],
            'publisher_name': publisher['name'],
            'publisher_url': publisher.get('url', ''),
            'homepage_url': item['homepage'],
            'support_url': item['support'],
            'icon_url': item['icon'],
            'capabilities': list(item['capabilities']),
            'nav_template': dict(item['navigation']),
            'status': 'published',
            'baseline_installs': item['installCount'],
            'catalog_updated_on': date.fromisoformat(item['updatedAt']),
        }
        app, was_created = app_model.objects.update_or_create(slug=item['slug'], defaults=defaults)
        if was_created:
            created += 1
        else:
            updated += 1
        version_model.objects.update_or_create(
            app=app,
            version=item['version'],
            defaults={'changelog': item['changelog'], 'nav_template': None},
        )
        screenshot_model.objects.filter(app=app, image='').delete()
        for position, shot in enumerate(item['screenshots']):
            screenshot_model.objects.create(
                app=app,
                src=shot['src'],
                alt=shot['alt'],
                position=position,
            )
    return created, updated
