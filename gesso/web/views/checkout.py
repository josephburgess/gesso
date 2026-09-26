from uuid import UUID

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST
from inertia import location, render

from gesso.artworks.models import Artwork
from gesso.commerce.models import Order
from gesso.commerce.services import NotAvailable, cancel_checkout, start_checkout


@require_POST
def start(request: HttpRequest, slug: str) -> HttpResponse:
    artwork = get_object_or_404(Artwork.objects.published(), slug=slug)
    try:
        url = start_checkout(artwork, site_url=request.build_absolute_uri('/'))
    except NotAvailable:
        messages.error(request, "Sorry, this work isn't available to buy right now.")
        return redirect('work_show', slug)
    return location(url)


@require_GET
def success(request: HttpRequest) -> HttpResponse:
    order = Order.objects.select_related('artwork').filter(stripe_session_id=request.GET.get('session_id', '')).first()
    title = order.artwork.title if order else None
    return render(request, 'Checkout/Success', {'title': title}, template_data={'title': 'Thank you'})


@require_GET
def cancel(request: HttpRequest, order_id: UUID) -> HttpResponse:
    artwork = cancel_checkout(order_id)
    return redirect('work_show', artwork.slug) if artwork else redirect('home')
