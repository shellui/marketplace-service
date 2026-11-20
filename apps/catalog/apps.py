from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.catalog'
    label = 'catalog'
    verbose_name = 'Catalog'

    def ready(self):
        from apps.catalog import schema  # noqa: F401
        from config import checks  # noqa: F401
