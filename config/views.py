from django.conf import settings
from django.shortcuts import render


def root(request):
    return render(
        request,
        'home.html',
        {
            'version': settings.VERSION,
            'github_url': 'https://github.com/shellui/marketplace-service',
            'directory_url': 'https://github.com/shellui/marketplace',
            'docs_url': 'https://docs.shellui.com/marketplace',
            'website_url': 'https://shellui.com',
        },
    )
