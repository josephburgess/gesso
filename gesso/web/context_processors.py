from django.conf import settings
from django.http import HttpRequest

from gesso.content.models import SiteContent
from gesso.web.appearance import appearance


def site(request: HttpRequest) -> dict[str, str | bool]:
    content = SiteContent.load()
    look = appearance(request, content)
    return {
        'site_name': content.site_name,
        'page_url': request.build_absolute_uri(request.path),
        'site_description': content.site_description,
        'site_theme': look['theme'],
        'site_headings': look['headings'],
        'site_motion': look['motion'],
    }


def sentry(request: HttpRequest) -> dict[str, str]:
    return {'sentry_frontend_dsn': settings.SENTRY_FRONTEND_DSN, 'sentry_environment': settings.SENTRY_ENVIRONMENT}
