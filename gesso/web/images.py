from typing import TypedDict

from gesso.artworks.models import ProcessedImage


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
