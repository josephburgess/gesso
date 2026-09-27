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
from gesso.enquiries.models import Topic
from gesso.web.formatting import dimensions, paragraphs, price


class ImageProps(TypedDict):
    src: str
    srcset: str
    width: int
    height: int
    thumb: str
    alt: str


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
        'thumb': url(image.variants[0]['name']),
        'alt': image.alt,
    }


def _cover(artwork: Artwork) -> ImageProps | None:
    return responsive_image(artwork.cover) if artwork.cover else None


class ArtworkTile(TypedDict):
    title: str
    year: int
    href: str
    cover: ImageProps | None
    status: str
    available: bool
    medium: str
    size: str
    price: str | None


def _price(artwork: Artwork) -> str | None:
    return price(artwork.price_pence) if artwork.status == ArtworkStatus.AVAILABLE and artwork.price_pence else None


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
        'price': _price(artwork),
    }


class ArtworkDetail(TypedDict):
    title: str
    year: int
    medium: str
    size: str
    framing: str
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
        'framing': artwork.framing,
        'status': artwork.display_status,
        'available': artwork.is_purchasable,
        'price': _price(artwork),
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


class Neighbour(TypedDict):
    title: str
    href: str


def _neighbours(artwork: Artwork) -> tuple[Neighbour | None, Neighbour | None]:
    works = list(Artwork.objects.published().values_list('slug', 'title'))
    if len(works) < 2:
        return None, None
    i = next(i for i, (slug, _) in enumerate(works) if slug == artwork.slug)
    prev, next_ = works[i - 1], works[(i + 1) % len(works)]
    return (
        {'title': prev[1], 'href': reverse('work_show', args=[prev[0]])},
        {'title': next_[1], 'href': reverse('work_show', args=[next_[0]])},
    )


class Purchase(TypedDict):
    action: str | None
    note: str
    enquire_href: str
    enquire_label: str
    notify: bool


def _purchase(artwork: Artwork, content: SiteContent) -> Purchase:
    if artwork.is_purchasable:
        delivery = f'Plus {price(content.delivery_pence)} UK delivery.' if content.delivery_pence else 'Includes UK delivery.'
        note = f'{delivery} Outside the UK, please enquire. Payment is handled by Stripe.'
    elif artwork.status == ArtworkStatus.AVAILABLE and artwork.is_reserved:
        note = 'Reserved pending payment.'
    else:
        note = ''
    sold = artwork.status == ArtworkStatus.SOLD
    query = {'artwork': artwork.slug} | ({'topic': Topic.COMMISSION} if sold else {})
    return {
        'action': reverse('checkout', args=[artwork.slug]) if artwork.is_purchasable else None,
        'note': note,
        'enquire_href': reverse('contact') + '?' + urlencode(query),
        'enquire_label': 'Ask about a commission' if sold else 'Enquire about this work',
        'notify': sold,
    }


@require_GET
def index(request: HttpRequest) -> HttpResponse:
    artworks = Artwork.objects.published().prefetch_related('images')
    return render(request, 'Work/Index', {'artworks': [artwork_tile(a) for a in artworks]}, template_data={'title': 'Work'})


def _structured_data(request: HttpRequest, artwork: Artwork, detail: ArtworkDetail, content: SiteContent) -> SafeString:
    creator: dict[str, str | list[str]] = {'@type': 'Person', 'name': content.site_name}
    if same_as := [link.url for link in content.social_links.all()]:
        creator['sameAs'] = same_as
    data = {
        '@context': 'https://schema.org',
        '@type': 'VisualArtwork',
        'name': artwork.title,
        'url': request.build_absolute_uri(artwork.get_absolute_url()),
        'dateCreated': str(artwork.year),
        'artMedium': artwork.medium,
        'creator': creator,
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
    prev, next_ = _neighbours(artwork)
    return render(
        request,
        'Work/Show',
        {'artwork': detail, 'purchase': _purchase(artwork, content), 'prev': prev, 'next': next_},
        template_data=_artwork_meta(request, detail) | {'structured_data': _structured_data(request, artwork, detail, content)},
    )
