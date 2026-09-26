import json
from decimal import Decimal
from typing import TypedDict
from urllib.parse import urlencode

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.safestring import SafeString, mark_safe
from django.utils.text import Truncator
from django.views.decorators.http import require_GET
from inertia import render

from gesso.artworks.models import Artwork, ArtworkStatus, ProcessedImage
from gesso.content.models import SiteContent
from gesso.web.formatting import dimensions, paragraphs, price


class ImageProps(TypedDict):
    src: str
    srcset: str
    width: int
    height: int


def responsive_image(image: ProcessedImage) -> ImageProps | None:
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


def _cover(artwork: Artwork) -> ImageProps | None:
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
        'status': artwork.display_status,
        'available': artwork.is_purchasable,
        'cover': _cover(artwork),
        'medium': artwork.medium,
        'size': dimensions(artwork.height_mm, artwork.width_mm),
    }


class ArtworkDetail(TypedDict):
    title: str
    year: int
    medium: str
    size: str
    images: list[ImageProps]
    status: str
    available: bool
    price: str | None
    description: list[str]


def _artwork_detail(artwork: Artwork) -> ArtworkDetail:
    return {
        'title': artwork.title,
        'year': artwork.year,
        'medium': artwork.medium,
        'size': dimensions(artwork.height_mm, artwork.width_mm),
        'status': artwork.display_status,
        'available': artwork.is_purchasable,
        'price': price(artwork.price_pence) if artwork.status == ArtworkStatus.AVAILABLE and artwork.price_pence else None,
        'images': [image for image in map(responsive_image, artwork.images.all()) if image],
        'description': paragraphs(artwork.description),
    }


def _artwork_meta(request: HttpRequest, detail: ArtworkDetail) -> dict[str, str]:
    description, images = detail['description'], detail['images']
    return {
        'title': detail['title'],
        'description': Truncator(description[0]).chars(155) if description else '',
        'image': request.build_absolute_uri(images[0]['src']) if images else '',
    }


class Purchase(TypedDict):
    action: str | None
    note: str
    enquire_href: str
    enquire_label: str


def _purchase(artwork: Artwork, content: SiteContent) -> Purchase:
    if artwork.is_purchasable:
        delivery = f'Plus {price(content.delivery_pence)} UK delivery.' if content.delivery_pence else 'Includes UK delivery.'
        note = f'{delivery} Outside the UK, please enquire. Payment is handled by Stripe.'
    elif artwork.status == ArtworkStatus.AVAILABLE and artwork.is_reserved:
        note = 'Reserved pending payment.'
    else:
        note = ''
    return {
        'action': reverse('checkout', args=[artwork.slug]) if artwork.is_purchasable else None,
        'note': note,
        'enquire_href': reverse('contact') + '?' + urlencode({'artwork': artwork.slug}),
        'enquire_label': 'Enquire about similar work' if artwork.status == ArtworkStatus.SOLD else 'Enquire about this work',
    }


@require_GET
def index(request: HttpRequest) -> HttpResponse:
    artworks = Artwork.objects.published().prefetch_related('images')
    return render(request, 'Work/Index', {'artworks': [artwork_tile(a) for a in artworks]}, template_data={'title': 'Work'})


def _structured_data(request: HttpRequest, artwork: Artwork, detail: ArtworkDetail, artist: str) -> SafeString:
    data = {
        '@context': 'https://schema.org',
        '@type': 'VisualArtwork',
        'name': artwork.title,
        'url': request.build_absolute_uri(artwork.get_absolute_url()),
        'dateCreated': str(artwork.year),
        'artMedium': artwork.medium,
        'creator': {'@type': 'Person', 'name': artist},
        'height': {'@type': 'QuantitativeValue', 'value': artwork.height_mm / 10, 'unitCode': 'CMT'},
        'width': {'@type': 'QuantitativeValue', 'value': artwork.width_mm / 10, 'unitCode': 'CMT'},
    }
    if detail['description']:
        data['description'] = ' '.join(detail['description'])
    if detail['images']:
        data['image'] = [request.build_absolute_uri(image['src']) for image in detail['images']]
    if artwork.status in (ArtworkStatus.AVAILABLE, ArtworkStatus.SOLD) and artwork.price_pence:
        data['offers'] = {
            '@type': 'Offer',
            'price': str(Decimal(artwork.price_pence) / 100),
            'priceCurrency': 'GBP',
            'availability': 'https://schema.org/SoldOut' if artwork.status == ArtworkStatus.SOLD else 'https://schema.org/InStock',
            'url': data['url'],
        }
    escaped = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return mark_safe(escaped)


@require_GET
def show(request: HttpRequest, slug: str) -> HttpResponse:
    artwork = get_object_or_404(Artwork.objects.published(), slug=slug)
    content = SiteContent.load()
    detail = _artwork_detail(artwork)
    return render(
        request,
        'Work/Show',
        {'artwork': detail, 'purchase': _purchase(artwork, content)},
        template_data=_artwork_meta(request, detail) | {'structured_data': _structured_data(request, artwork, detail, content.site_name)},
    )
