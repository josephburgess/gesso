import json

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_http_methods
from inertia import render

from gesso.artworks.models import Artwork
from gesso.content.models import SiteContent
from gesso.enquiries.forms import EnquiryForm
from gesso.enquiries.services import submit_enquiry
from gesso.web import props


@require_GET
def home(request: HttpRequest) -> HttpResponse:
    return render(request, 'Home')


@require_GET
def work_index(request: HttpRequest) -> HttpResponse:
    artworks = Artwork.objects.published().prefetch_related('images')
    return render(request, 'Work/Index', {'artworks': [props.artwork_tile(a) for a in artworks]})


@require_GET
def work_show(request: HttpRequest, slug: str) -> HttpResponse:
    artwork = get_object_or_404(Artwork.objects.published(), slug=slug)
    return render(request, 'Work/Show', {'artwork': props.artwork_detail(artwork)})


@require_GET
def about(request: HttpRequest) -> HttpResponse:
    return render(request, 'About', {'about': props.about(SiteContent.load())})


@require_http_methods(['GET', 'POST'])
def contact(request: HttpRequest) -> HttpResponse:
    data = None
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except ValueError:
            data = None
        if not isinstance(data, dict):
            return HttpResponseBadRequest()
    form = EnquiryForm(data)
    if form.is_valid():
        if not form.is_spam():
            submit_enquiry(form)
        messages.success(request, 'Thanks, your message is on its way.')
        return redirect('contact')
    return render(request, 'Contact', {'contact': props.contact(SiteContent.load()), 'errors': props.form_errors(form)})
