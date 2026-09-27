from typing import TypedDict

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_GET
from inertia import render

from gesso.artworks.models import Artwork, ArtworkImage
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


def _process() -> list[ProcessPhoto]:
    photos = (
        ArtworkImage.objects.filter(artwork__is_published=True)
        .exclude(home_position=None)
        .select_related('artwork')
        .order_by('home_position')[:2]
    )
    return [
        {'image': image, 'caption': photo.caption, 'title': photo.artwork.title}
        for photo in photos
        if photo.artwork and (image := responsive_image(photo))
    ]


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
        'process': _process(),
    }
    lead = home['featured'][0]['cover'] if home['featured'] else None
    return render(request, 'Home', {'home': home}, template_data={'image': request.build_absolute_uri(lead['src']) if lead else ''})
