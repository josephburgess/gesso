from typing import TypedDict

from django.urls import reverse

from gesso.artworks.models import Artwork, ArtworkImage


class ImageProps(TypedDict):
    src: str
    srcset: str
    width: int
    height: int


class ArtworkTile(TypedDict):
    title: str
    year: int
    href: str
    cover: ImageProps | None


class ArtworkDetail(TypedDict):
    title: str
    year: int
    cover: ImageProps | None


class NavLink(TypedDict):
    label: str
    href: str
    current: bool


class Site(TypedDict):
    name: str
    tagline: str
    home_href: str
    nav: list[NavLink]


def _in_section(path: str, href: str) -> bool:
    return path == href or path.startswith(href + '/')


def site_props(path: str) -> Site:
    nav = [('Work', reverse('work'))]
    return {
        'name': 'Elise Beer',
        'tagline': 'Painter',
        'home_href': reverse('home'),
        'nav': [{'label': label, 'href': href, 'current': _in_section(path, href)} for label, href in nav],
    }


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


def artwork_tile(artwork: Artwork) -> ArtworkTile:
    return {
        'title': artwork.title,
        'year': artwork.year,
        'href': reverse('work_show', args=[artwork.slug]),
        'cover': _cover(artwork),
    }


def artwork_detail(artwork: Artwork) -> ArtworkDetail:
    return {
        'title': artwork.title,
        'year': artwork.year,
        'cover': _cover(artwork),
    }
