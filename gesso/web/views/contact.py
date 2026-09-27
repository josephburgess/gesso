from typing import TypedDict

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
from inertia import render

from gesso.artworks.models import Artwork
from gesso.content.models import SiteContent
from gesso.enquiries.forms import EnquiryForm
from gesso.enquiries.models import Topic
from gesso.enquiries.services import submit_enquiry
from gesso.web.views.forms import form_errors, json_body


class EnquiryArtwork(TypedDict):
    title: str
    slug: str


class Choice(TypedDict):
    value: str
    label: str


class Contact(TypedDict):
    details: str
    action: str
    artwork: EnquiryArtwork | None
    topics: list[Choice]
    topic: str


@require_http_methods(['GET', 'POST'])
@ratelimit(key='ip', rate='5/h', method='POST', block=False)
def page(request: HttpRequest) -> HttpResponse:
    if getattr(request, 'limited', False):
        messages.error(request, "You've sent a few messages already. Please try again in an hour.")
        return redirect('contact')

    data = None

    if request.method == 'POST' and (data := json_body(request)) is None:
        return HttpResponseBadRequest()

    form = EnquiryForm(data)

    if form.is_valid():
        if not form.is_spam():
            submit_enquiry(form)
        messages.success(request, 'Thanks, your message is on its way.')
        return redirect('contact')

    slug = (data or request.GET).get('artwork')
    artwork = Artwork.objects.published().filter(slug=slug).first()
    topic = request.GET.get('topic', '')
    contact: Contact = {
        'details': SiteContent.load().contact_details,
        'action': reverse('contact'),
        'artwork': {'title': artwork.title, 'slug': artwork.slug} if artwork else None,
        'topics': [{'value': value, 'label': label} for value, label in Topic.choices],
        'topic': topic if topic in Topic.values else Topic.BUYING if artwork else Topic.GENERAL,
    }
    return render(
        request,
        'Contact',
        {'contact': contact, 'errors': form_errors(form)},
        template_data={'title': 'Contact'},
    )
