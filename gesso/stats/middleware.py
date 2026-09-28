import re
from urllib.parse import urlsplit

from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.urls import ResolverMatch
from django.utils import timezone
from django.utils.crypto import salted_hmac

from gesso.artworks.models import Artwork
from gesso.stats.models import DailyReferrer, DailyView, DailyVisitors, increment
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


def visitor_id(request: HttpRequest, day) -> str:
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[0].strip()
    return salted_hmac(f'gesso.stats.visitor.{day}', ip + request.headers.get('User-Agent', ''), algorithm='sha256').hexdigest()


def first_time(*parts) -> bool:
    return cache.add(':'.join(map(str, ('stats', *parts))), True, timeout=60 * 60 * 24)


def get_artwork(match: ResolverMatch) -> Artwork | None:
    return Artwork.objects.filter(slug=match.kwargs['slug']).first() if match.url_name == 'work_show' else None


def count_views(get_response):
    def middleware(request):
        response = get_response(request)
        if is_visit(request, response):
            day = timezone.localdate()
            visitor = visitor_id(request, day)
            if first_time(day, visitor):
                increment(DailyVisitors, 'visitors', day=day)
            if first_time(day, visitor, request.path):
                increment(DailyView, 'views', defaults={'artwork': get_artwork(request.resolver_match)}, day=day, path=request.path)
            host = urlsplit(request.headers.get('Referer', '')).hostname
            if host and host != request.get_host().split(':')[0]:
                increment(DailyReferrer, 'visits', day=day, host=host.removeprefix('www.'))
        return response

    return middleware
