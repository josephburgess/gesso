from typing import TypedDict

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_GET
from inertia import render

from gesso.artworks.models import Artwork
from gesso.content.models import SiteContent
from gesso.web.views.work import ArtworkTile, artwork_tile


class Home(TypedDict):
    intro: str
    statement: str
    about_href: str
    featured: list[ArtworkTile]
    index: list[ArtworkTile]


def props(content: SiteContent, artworks: list[Artwork]) -> Home:
    featured = sorted((a for a in artworks if a.featured_order is not None), key=lambda a: a.featured_order or 0)
    return {
        'intro': content.intro,
        'statement': content.statement,
        'about_href': reverse('about'),
        'featured': [artwork_tile(a) for a in featured],
        'index': [artwork_tile(a) for a in artworks],
    }


@require_GET
def page(request: HttpRequest) -> HttpResponse:
    artworks = list(Artwork.objects.published().prefetch_related('images'))
    return render(request, 'Home', {'home': props(SiteContent.load(), artworks)})
