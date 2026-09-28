import re
from urllib.parse import urlsplit

from django.http import HttpRequest, HttpResponse
from django.utils import timezone

from gesso.artworks.models import Artwork
from gesso.stats.models import DailyReferrer, DailyView
from gesso.web.appearance import is_preview

PUBLIC_PAGES = {'home', 'work', 'work_show', 'about', 'contact', 'page'}
BOTS = re.compile(r'bot|crawl|spider|slurp|preview|facebookexternalhit', re.IGNORECASE)


def is_visit(request: HttpRequest, response: HttpResponse) -> bool:
    match = request.resolver_match
    return (
        request.method == 'GET'
        and response.status_code == 200
        and match is not None
        and match.url_name in PUBLIC_PAGES
        and not request.user.is_staff
        and not is_preview(request)
        and 'X-Inertia-Partial-Data' not in request.headers
        and 'prefetch' not in request.headers.get('Sec-Purpose', request.headers.get('Purpose', ''))
        and not BOTS.search(request.headers.get('User-Agent', ''))
    )


def count_views(get_response):
    def middleware(request):
        response = get_response(request)
        if is_visit(request, response):
            day = timezone.localdate()
            match = request.resolver_match
            artwork = Artwork.objects.filter(slug=match.kwargs['slug']).first() if match.url_name == 'work_show' else None
            DailyView.record(day, request.path, artwork)
            host = urlsplit(request.headers.get('Referer', '')).hostname
            if host and host != request.get_host().split(':')[0]:
                DailyReferrer.record(day, host.removeprefix('www.'))
        return response

    return middleware
