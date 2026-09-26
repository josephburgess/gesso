from django.http import HttpRequest

from gesso.content.models import SiteContent


def site(request: HttpRequest) -> dict[str, str]:
    content = SiteContent.load()
    return {'site_name': content.site_name, 'site_description': content.site_description}
