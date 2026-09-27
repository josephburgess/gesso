from typing import TypedDict

from django.db import models
from django.http import HttpRequest, QueryDict

from gesso.content.models import AboutLayout, Headings, SiteContent, SiteLayout, Theme, WorkLayout


class Appearance(TypedDict):
    theme: str
    layout: str
    work_layout: str
    headings: str
    motion: bool
    show_index: bool
    about_layout: str


def _query(request: HttpRequest) -> QueryDict:
    return QueryDict(request.META.get('QUERY_STRING', ''))


def is_preview(request: HttpRequest) -> bool:
    return _query(request).get('preview') == '1' and request.user.is_staff


def appearance(request: HttpRequest, content: SiteContent) -> Appearance:
    query = _query(request) if is_preview(request) else QueryDict()

    def pick(field: str, choices: type[models.TextChoices]) -> str:
        value = query.get(field, '')
        return value if value in choices.values else getattr(content, field)

    def switch(param: str, saved: bool) -> bool:
        value = query.get(param)
        return value == 'on' if value in ('on', 'off') else saved

    return {
        'theme': pick('theme', Theme),
        'layout': pick('layout', SiteLayout),
        'work_layout': pick('work_layout', WorkLayout),
        'headings': pick('headings', Headings),
        'motion': switch('motion', content.motion),
        'show_index': switch('index', content.show_index),
        'about_layout': pick('about_layout', AboutLayout),
    }
