from typing import TypedDict

from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET
from inertia import render

from gesso.content.models import SiteContent
from gesso.web.formatting import paragraphs
from gesso.web.views.work import ImageProps, responsive_image


class Photo(TypedDict):
    image: ImageProps
    alt: str
    caption: str


class About(TypedDict):
    statement: str
    biography: list[str]
    photos: list[Photo]


@require_GET
def page(request: HttpRequest) -> HttpResponse:
    content = SiteContent.load()
    about: About = {
        'statement': content.statement,
        'biography': paragraphs(content.biography),
        'photos': [
            {'image': image, 'alt': photo.alt, 'caption': photo.caption}
            for photo in content.about_images.all()
            if (image := responsive_image(photo))
        ],
    }
    return render(request, 'About', {'about': about}, template_data={'title': 'About'})
