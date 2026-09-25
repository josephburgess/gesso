from typing import TypedDict

from django.conf import settings
from django.urls import reverse
from inertia import share


class NavLink(TypedDict):
    label: str
    href: str
    current: bool


class Site(TypedDict):
    name: str
    tagline: str
    home_href: str
    nav: list[NavLink]


def site_props(path: str) -> Site:
    nav = [('Work', reverse('work')), ('About', reverse('about')), ('Contact', reverse('contact'))]
    return {
        'name': 'Elise Beer',
        'tagline': 'Painter',
        'home_href': reverse('home'),
        'nav': [{'label': label, 'href': href, 'current': _in_section(path, href)} for label, href in nav],
    }


def _in_section(path: str, href: str) -> bool:
    return path == href or path.startswith(href + '/')


def share_site(get_response):
    def middleware(request):
        share(request, site=site_props(request.path))
        return get_response(request)

    return middleware


def noindex(get_response):
    def middleware(request):
        response = get_response(request)
        if settings.NOINDEX:
            response['X-Robots-Tag'] = 'noindex, nofollow'
        return response

    return middleware
