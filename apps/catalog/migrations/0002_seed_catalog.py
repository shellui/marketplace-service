"""Load the directory seed so a fresh migrate matches the Shellui Marketplace UI."""

from django.db import migrations


def forwards(apps, schema_editor):
    from apps.catalog.seed import seed_marketplace

    seed_marketplace(apps=apps)


def backwards(apps, schema_editor):
    apps.get_model('catalog', 'App').objects.all().delete()
    apps.get_model('catalog', 'Category').objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
