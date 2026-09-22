from typing import TypedDict

from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET
from inertia import render

from gesso.content.models import SiteContent
from gesso.web.formatting import paragraphs


class About(TypedDict):
    statement: str
    biography: list[str]


@require_GET
def page(request: HttpRequest) -> HttpResponse:
    content = SiteContent.load()
    about: About = {'statement': content.statement, 'biography': paragraphs(content.biography)}
    return render(request, 'About', {'about': about}, template_data={'title': 'About'})
