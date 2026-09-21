from typing import TypedDict

from django.forms import BaseForm
from django.http import HttpRequest
from django.urls import reverse
from django.utils.text import Truncator

from gesso.artworks.models import Artwork, ArtworkImage, ArtworkStatus
from gesso.content.models import SiteContent
from gesso.web.formatting import dimensions, paragraphs, price


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
        'status': ArtworkStatus(artwork.status).label,
        'available': artwork.status == ArtworkStatus.AVAILABLE,
        'cover': _cover(artwork),
        'medium': artwork.medium,
        'size': dimensions(artwork.height_mm, artwork.width_mm),
    }


def form_errors(form: BaseForm) -> dict[str, str]:
    return {field: errors[0] for field, errors in form.errors.get_json_data().items()}


class Home(TypedDict):
    intro: str
    statement: str
    about_href: str
    featured: list[ArtworkTile]
    index: list[ArtworkTile]


def home(content: SiteContent, artworks: list[Artwork]) -> Home:
    featured = sorted((a for a in artworks if a.featured_order is not None), key=lambda a: a.featured_order or 0)
    return {
        'intro': content.intro,
        'statement': content.statement,
        'about_href': reverse('about'),
        'featured': [artwork_tile(a) for a in featured],
        'index': [artwork_tile(a) for a in artworks],
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
        'cover': _cover(artwork),
        'description': paragraphs(artwork.description),
    }


def artwork_meta(request: HttpRequest, detail: ArtworkDetail) -> dict[str, str]:
    """Title, description and image for the server-rendered <head>, for link previews."""
    description, cover = detail['description'], detail['cover']
    return {
        'title': detail['title'],
        'description': Truncator(description[0]).chars(155) if description else '',
        'image': request.build_absolute_uri(cover['src']) if cover else '',
    }


class About(TypedDict):
    statement: str
    biography: list[str]


def about(content: SiteContent) -> About:
    return {
        'statement': content.statement,
        'biography': paragraphs(content.biography),
    }


class EnquiryArtwork(TypedDict):
    title: str
    slug: str


class Contact(TypedDict):
    details: str
    action: str
    artwork: EnquiryArtwork | None


def contact(content: SiteContent, artwork: Artwork | None) -> Contact:
    return {
        'details': content.contact_details,
        'action': reverse('contact'),
        'artwork': {'title': artwork.title, 'slug': artwork.slug} if artwork else None,
    }
