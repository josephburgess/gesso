import json
from typing import TypedDict

from django.contrib import messages
from django.forms import BaseForm
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from inertia import render

from gesso.artworks.models import Artwork
from gesso.content.models import SiteContent
from gesso.enquiries.forms import EnquiryForm
from gesso.enquiries.services import submit_enquiry


class EnquiryArtwork(TypedDict):
    title: str
    slug: str


class Contact(TypedDict):
    details: str
    action: str
    artwork: EnquiryArtwork | None


def props(content: SiteContent, artwork: Artwork | None) -> Contact:
    return {
        'details': content.contact_details,
        'action': reverse('contact'),
        'artwork': {'title': artwork.title, 'slug': artwork.slug} if artwork else None,
    }


@require_http_methods(['GET', 'POST'])
def page(request: HttpRequest) -> HttpResponse:
    data = None

    if request.method == 'POST' and (data := _json_body(request)) is None:
        return HttpResponseBadRequest()

    form = EnquiryForm(data)

    if form.is_valid():
        if not form.is_spam():
            submit_enquiry(form)
        messages.success(request, 'Thanks, your message is on its way.')
        return redirect('contact')

    slug = (data or request.GET).get('artwork')
    artwork = Artwork.objects.published().filter(slug=slug).first()
    return render(
        request,
        'Contact',
        {'contact': props(SiteContent.load(), artwork), 'errors': _form_errors(form)},
        template_data={'title': 'Contact'},
    )


def _json_body(request: HttpRequest) -> dict | None:
    try:
        data = json.loads(request.body)
    except ValueError, UnicodeDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _form_errors(form: BaseForm) -> dict[str, str]:
    return {field: errors[0] for field, errors in form.errors.get_json_data().items()}
