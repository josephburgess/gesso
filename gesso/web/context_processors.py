from django.conf import settings
from django.http import HttpRequest

from gesso.content.models import SiteContent


def site(request: HttpRequest) -> dict[str, str]:
    content = SiteContent.load()
    return {'site_name': content.site_name, 'site_description': content.site_description}


def sentry(request: HttpRequest) -> dict[str, str]:
    return {'sentry_frontend_dsn': settings.SENTRY_FRONTEND_DSN, 'sentry_environment': settings.SENTRY_ENVIRONMENT}
