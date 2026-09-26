from typing import TypedDict

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_GET
from inertia import render

from gesso.artworks.models import Artwork
from gesso.content.models import SiteContent
from gesso.web.views.work import ArtworkTile, ImageProps, artwork_tile, responsive_image


class ProcessPhoto(TypedDict):
    image: ImageProps
    caption: str
    title: str


class Home(TypedDict):
    intro: str
    statement: str
    about_href: str
    featured: list[ArtworkTile]
    index: list[ArtworkTile]
    process: list[ProcessPhoto]


def _process(artworks: list[Artwork]) -> list[ProcessPhoto]:
    photos: list[ProcessPhoto] = [
        {'image': image, 'caption': photo.caption, 'title': artwork.title}
        for artwork in artworks
        for photo in artwork.images.all()
        if photo.is_process and (image := responsive_image(photo))
    ]
    return photos[:2]


@require_GET
def page(request: HttpRequest) -> HttpResponse:
    content = SiteContent.load()
    artworks = list(Artwork.objects.published().prefetch_related('images'))
    featured = sorted((a for a in artworks if a.featured_order is not None), key=lambda a: a.featured_order or 0)
    home: Home = {
        'intro': content.intro,
        'statement': content.statement,
        'about_href': reverse('about'),
        'featured': [artwork_tile(a) for a in featured],
        'index': [artwork_tile(a) for a in artworks],
        'process': _process(featured + [a for a in artworks if a.featured_order is None]),
    }
    return render(request, 'Home', {'home': home})
