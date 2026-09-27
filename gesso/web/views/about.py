from typing import TypedDict

from django.http import HttpRequest, HttpResponse
from django.utils.text import Truncator
from django.views.decorators.http import require_GET
from inertia import render

from gesso.content.models import SiteContent
from gesso.web.formatting import paragraphs
from gesso.web.images import ImageProps, responsive_image


class Photo(TypedDict):
    image: ImageProps
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
            {'image': image, 'caption': photo.caption} for photo in content.about_images.all() if (image := responsive_image(photo))
        ],
    }
    portrait = about['photos'][0]['image']['src'] if about['photos'] else None
    return render(
        request,
        'About',
        {'about': about},
        template_data={
            'title': 'About',
            'description': Truncator(about['statement'] or next(iter(about['biography']), '')).chars(155),
            'image': request.build_absolute_uri(portrait) if portrait else '',
        },
    )
