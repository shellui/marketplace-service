"""Django admin for curating the Shellui Marketplace catalog."""

from django.contrib import admin
from django.db.models import Count, Q
from django.shortcuts import render
from django.urls import path, reverse

from .models import App, AppInstall, AppScreenshot, AppVersion, Category, InstallEvent


class MarketplaceAdminSite(admin.AdminSite):
    site_header = 'Shellui Marketplace'
    site_title = 'Shellui Marketplace'
    index_title = 'Catalog'

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('analytics/', self.admin_view(self.analytics), name='analytics'),
        ]
        return custom + urls

    def analytics(self, request):
        apps = (
            App.objects.select_related('category')
            .annotate(active_installs=Count('installs', filter=Q(installs__active=True)))
            .order_by('-active_installs', 'name')
        )
        events = InstallEvent.objects.select_related('app').order_by('-created_at')[:50]
        context = {
            **self.each_context(request),
            'title': 'Install analytics',
            'apps': apps,
            'events': events,
            'published': App.objects.filter(status=App.STATUS_PUBLISHED).count(),
            'active_total': AppInstall.objects.filter(active=True).count(),
        }
        return render(request, 'admin/catalog/analytics.html', context)


admin_site = MarketplaceAdminSite(name='marketplace')


class AppVersionInline(admin.StackedInline):
    model = AppVersion
    extra = 0
    fields = ('version', 'changelog', 'nav_template', 'created_at')
    readonly_fields = ('created_at',)


class AppScreenshotInline(admin.TabularInline):
    model = AppScreenshot
    extra = 1
    fields = ('position', 'image', 'src', 'alt')
    ordering = ('position', 'id')


@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('label', 'slug', 'position')
    prepopulated_fields = {'slug': ('label',)}
    ordering = ('position', 'label')


@admin.register(App, site=admin_site)
class AppAdmin(admin.ModelAdmin):
    change_list_template = 'admin/catalog/app_change_list.html'
    list_display = (
        'name',
        'slug',
        'category',
        'is_official',
        'is_verified',
        'status',
        'active_installs',
        'catalog_updated_on',
    )
    list_filter = ('status', 'is_official', 'is_verified', 'category', 'featured')
    search_fields = ('name', 'slug', 'publisher_name', 'tagline')
    inlines = [AppVersionInline, AppScreenshotInline]
    readonly_fields = ('created_at', 'updated_at', 'active_installs')
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'tagline', 'description', 'category', 'tags', 'status')}),
        ('Publisher', {'fields': ('is_official', 'is_verified', 'featured', 'publisher_name', 'publisher_url')}),
        ('Links', {'fields': ('homepage_url', 'support_url', 'icon_url', 'icon')}),
        ('Shell', {'fields': ('capabilities', 'nav_template')}),
        (
            'Stats',
            {
                'fields': (
                    'baseline_installs',
                    'active_installs',
                    'catalog_updated_on',
                    'created_at',
                    'updated_at',
                )
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _active_installs=Count('installs', filter=Q(installs__active=True))
        )

    @admin.display(description='Active installs', ordering='_active_installs')
    def active_installs(self, obj):
        return getattr(obj, '_active_installs', obj.installs.filter(active=True).count())

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['analytics_url'] = reverse('marketplace:analytics')
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(AppInstall, site=admin_site)
class AppInstallAdmin(admin.ModelAdmin):
    list_display = ('app', 'kind', 'active', 'subject_hash', 'updated_at')
    list_filter = ('kind', 'active', 'app')
    search_fields = ('subject_hash', 'app__slug')
    readonly_fields = ('app', 'subject_hash', 'kind', 'active', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        return False


@admin.register(InstallEvent, site=admin_site)
class InstallEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'app', 'action', 'subject_hash')
    list_filter = ('action', 'app')
    search_fields = ('subject_hash', 'app__slug')
    readonly_fields = ('app', 'action', 'subject_hash', 'created_at')

    def has_add_permission(self, request):
        return False
