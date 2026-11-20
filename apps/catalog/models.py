"""Shellui Marketplace catalog models."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from .validation import (
    validate_absolute_url,
    validate_capabilities,
    validate_icon_reference,
    validate_nav_template,
    validate_optional_url,
    validate_slug,
    validate_tags,
    validate_version,
)


class Category(models.Model):
    slug = models.SlugField(max_length=40, unique=True)
    label = models.CharField(max_length=80)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position', 'label']
        verbose_name_plural = 'categories'

    def __str__(self) -> str:
        return self.label


class App(models.Model):
    STATUS_PUBLISHED = 'published'
    STATUS_UNLISTED = 'unlisted'
    STATUS_CHOICES = [
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_UNLISTED, 'Unlisted'),
    ]

    slug = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=80)
    tagline = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='apps')
    tags = models.JSONField(default=list, blank=True)
    is_official = models.BooleanField('Official Shellui app', default=False)
    is_verified = models.BooleanField('Verified publisher', default=False)
    featured = models.BooleanField(default=False)
    publisher_name = models.CharField(max_length=120)
    publisher_url = models.CharField(max_length=300, blank=True)
    homepage_url = models.CharField(max_length=300)
    support_url = models.CharField(max_length=300)
    icon_url = models.CharField(
        max_length=300,
        blank=True,
        help_text='Site path (/icons/files.svg), icon name, or https URL. Optional when an icon file is uploaded.',
    )
    icon = models.ImageField(upload_to='icons/', blank=True)
    capabilities = models.JSONField(default=list)
    nav_template = models.JSONField('Navigation item template')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PUBLISHED)
    baseline_installs = models.PositiveIntegerField(
        default=0,
        help_text='Curated install count from the directory seed. Live active installs are added on top.',
    )
    catalog_updated_on = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    def clean(self):
        self.slug = validate_slug(self.slug)
        self.tags = validate_tags(self.tags)
        if len(self.description or '') > 20000:
            raise ValidationError({'description': 'Description is too long.'})
        self.publisher_url = validate_optional_url(self.publisher_url, field='Publisher URL')
        self.homepage_url = validate_absolute_url(self.homepage_url, field='Homepage')
        self.support_url = validate_absolute_url(self.support_url, field='Support URL')
        self.icon_url = validate_icon_reference(self.icon_url, field='Icon')
        if not self.icon and not self.icon_url:
            raise ValidationError({'icon_url': 'Add an icon file or an icon path.'})
        self.capabilities = validate_capabilities(self.capabilities, official=self.is_official)
        self.nav_template = validate_nav_template(self.nav_template, official=self.is_official)
        if self.nav_template.get('safeForAuthToken') and 'auth' not in self.capabilities:
            raise ValidationError(
                {'nav_template': 'safeForAuthToken requires the auth capability, and only on an official app.'}
            )
        if self.is_official and self.is_verified:
            raise ValidationError('An official Shellui app is not also marked as a verified third party.')

    @property
    def publisher_kind(self) -> str:
        if self.is_official:
            return 'official'
        if self.is_verified:
            return 'verified'
        return 'community'


class AppVersion(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='versions')
    version = models.CharField(max_length=32)
    changelog = models.TextField(blank=True)
    nav_template = models.JSONField(
        'Navigation item override',
        null=True,
        blank=True,
        help_text='Leave empty to keep the app navigation template.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [
            models.UniqueConstraint(fields=['app', 'version'], name='unique_app_version'),
        ]

    def __str__(self) -> str:
        return f'{self.app_id}:{self.version}'

    def clean(self):
        self.version = validate_version(self.version)
        if len(self.changelog or '') > 8000:
            raise ValidationError({'changelog': 'Changelog is too long.'})
        if self.nav_template in ({}, None, ''):
            self.nav_template = None
            return
        official = bool(getattr(self.app, 'is_official', False))
        self.nav_template = validate_nav_template(self.nav_template, official=official)


class AppScreenshot(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='screenshots')
    image = models.ImageField(upload_to='screenshots/', blank=True)
    src = models.CharField(
        max_length=300,
        blank=True,
        help_text='Site path or https URL. Optional when an image file is uploaded.',
    )
    alt = models.CharField(max_length=200)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position', 'id']

    def __str__(self) -> str:
        return self.alt

    def clean(self):
        self.src = validate_icon_reference(self.src, field='Screenshot')
        if not self.image and not self.src:
            raise ValidationError('Upload a screenshot or set a src path.')
        if not (self.alt or '').strip():
            raise ValidationError({'alt': 'Alt text is required.'})


class AppInstall(models.Model):
    KIND_USER = 'user'
    KIND_ANONYMOUS = 'anonymous'
    KIND_CHOICES = [
        (KIND_USER, 'Signed-in user'),
        (KIND_ANONYMOUS, 'Anonymous install'),
    ]

    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='installs')
    subject_hash = models.CharField(max_length=64)
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['app', 'subject_hash'], name='unique_install_subject'),
        ]
        indexes = [
            models.Index(fields=['app', 'active']),
        ]

    def __str__(self) -> str:
        return f'{self.app_id}:{self.subject_hash[:8]}'


class InstallEvent(models.Model):
    ACTION_INSTALL = 'install'
    ACTION_UNINSTALL = 'uninstall'
    ACTION_CHOICES = [
        (ACTION_INSTALL, 'Install'),
        (ACTION_UNINSTALL, 'Uninstall'),
    ]

    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='events')
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    subject_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['app', 'action', 'created_at']),
        ]

    def __str__(self) -> str:
        return f'{self.action}:{self.subject_hash[:8]}'
