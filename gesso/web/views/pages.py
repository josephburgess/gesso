from typing import TypedDict

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from inertia import render

from gesso.content.models import Page
from gesso.web.formatting import paragraphs


class Block(TypedDict):
    heading: bool
    text: str


class PageProps(TypedDict):
    title: str
    blocks: list[Block]


def _block(paragraph: str) -> Block:
    if paragraph.startswith('##'):
        return {'heading': True, 'text': paragraph.lstrip('#').strip()}
    return {'heading': False, 'text': paragraph}


@require_GET
def show(request: HttpRequest, slug: str) -> HttpResponse:
    page = get_object_or_404(Page, slug=slug)
    props: PageProps = {'title': page.title, 'blocks': [_block(p) for p in paragraphs(page.body)]}
    return render(request, 'Page', {'page': props}, template_data={'title': page.title})
