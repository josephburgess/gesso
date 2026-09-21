from typing import TypedDict

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.text import Truncator
from django.views.decorators.http import require_GET
from inertia import render

from gesso.artworks.models import Artwork, ArtworkImage, ArtworkStatus
from gesso.web.formatting import dimensions, paragraphs, price


class ImageProps(TypedDict):
    src: str
    srcset: str
    width: int
    height: int


def responsive_image(image: ArtworkImage) -> ImageProps | None:
    if not image.variants:
        return None
    url = image.original.storage.url
    largest = image.variants[-1]
    return {
        'src': url(largest['name']),
        'srcset': ', '.join(f'{url(v["name"])} {v["width"]}w' for v in image.variants),
        'width': largest['width'],
        'height': largest['height'],
    }


def cover(artwork: Artwork) -> ImageProps | None:
    images = artwork.images.all()
    return responsive_image(images[0]) if images else None


class ArtworkTile(TypedDict):
    title: str
    year: int
    href: str
    cover: ImageProps | None
    status: str
    available: bool
    medium: str
    size: str


def artwork_tile(artwork: Artwork) -> ArtworkTile:
    return {
        'title': artwork.title,
        'year': artwork.year,
        'href': reverse('work_show', args=[artwork.slug]),
        'status': ArtworkStatus(artwork.status).label,
        'available': artwork.status == ArtworkStatus.AVAILABLE,
        'cover': cover(artwork),
        'medium': artwork.medium,
        'size': dimensions(artwork.height_mm, artwork.width_mm),
    }


class ArtworkDetail(TypedDict):
    title: str
    year: int
    medium: str
    size: str
    cover: ImageProps | None
    status: str
    available: bool
    price: str | None
    description: list[str]


def artwork_detail(artwork: Artwork) -> ArtworkDetail:
    available = artwork.status == ArtworkStatus.AVAILABLE
    return {
        'title': artwork.title,
        'year': artwork.year,
        'medium': artwork.medium,
        'size': dimensions(artwork.height_mm, artwork.width_mm),
        'status': ArtworkStatus(artwork.status).label,
        'available': available,
        'price': price(artwork.price_pence) if available and artwork.price_pence else None,
        'cover': cover(artwork),
        'description': paragraphs(artwork.description),
    }


def artwork_meta(request: HttpRequest, detail: ArtworkDetail) -> dict[str, str]:
    description, image = detail['description'], detail['cover']
    return {
        'title': detail['title'],
        'description': Truncator(description[0]).chars(155) if description else '',
        'image': request.build_absolute_uri(image['src']) if image else '',
    }


@require_GET
def index(request: HttpRequest) -> HttpResponse:
    artworks = Artwork.objects.published().prefetch_related('images')
    return render(request, 'Work/Index', {'artworks': [artwork_tile(a) for a in artworks]}, template_data={'title': 'Work'})


@require_GET
def show(request: HttpRequest, slug: str) -> HttpResponse:
    artwork = get_object_or_404(Artwork.objects.published(), slug=slug)
    detail = artwork_detail(artwork)
    return render(request, 'Work/Show', {'artwork': detail}, template_data=artwork_meta(request, detail))
