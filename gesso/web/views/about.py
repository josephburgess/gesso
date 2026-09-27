from typing import TypedDict

from django.http import HttpRequest, HttpResponse
from django.utils.text import Truncator
from django.views.decorators.http import require_GET
from inertia import render

from gesso.content.models import CVKind, SiteContent
from gesso.web.formatting import paragraphs
from gesso.web.views.work import ImageProps, responsive_image


class Photo(TypedDict):
    image: ImageProps
    caption: str


class CVItem(TypedDict):
    year: int
    title: str
    where: str
    link: str


class CVGroup(TypedDict):
    label: str
    entries: list[CVItem]


class About(TypedDict):
    statement: str
    biography: list[str]
    photos: list[Photo]
    cv: list[CVGroup]


def _cv(content: SiteContent) -> list[CVGroup]:
    entries = list(content.cv_entries.all())
    groups: list[CVGroup] = [
        {
            'label': kind.label,
            'entries': [
                {'year': e.year, 'title': e.title, 'where': ', '.join(filter(None, (e.venue, e.place))), 'link': e.link}
                for e in entries
                if e.kind == kind
            ],
        }
        for kind in CVKind
    ]
    return [group for group in groups if group['entries']]


@require_GET
def page(request: HttpRequest) -> HttpResponse:
    content = SiteContent.load()
    about: About = {
        'statement': content.statement,
        'biography': paragraphs(content.biography),
        'cv': _cv(content),
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
