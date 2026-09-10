from typing import TypedDict

from django.urls import reverse

from gesso.artworks.models import Artwork


class ArtworkTile(TypedDict):
    title: str
    year: int
    href: str
    cover: str | None


class ArtworkDetail(TypedDict):
    title: str
    year: int
    cover: str | None

def _cover(artwork: Artwork) -> str | None:
    images = artwork.images.all()
    return images[0].original.url if images else None


def artwork_tile(artwork: Artwork) -> ArtworkTile:
    return {
        "title": artwork.title,
        "year": artwork.year,
        "href": reverse("work_show", args=[artwork.slug]),
        "cover": _cover(artwork),
    }


def artwork_detail(artwork: Artwork) -> ArtworkDetail:
    return {
        "title": artwork.title,
        "year": artwork.year,
        "cover": _cover(artwork),
    }
