from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from gesso.artworks.models import Artwork
from gesso.commerce import stripe_client
from gesso.commerce.models import Order
from gesso.content.models import SiteContent

RESERVATION = timedelta(minutes=31)


class NotAvailable(Exception):
    pass


@transaction.atomic
def start_checkout(artwork: Artwork, success_url: str, cancel_url: str) -> str:
    artwork.refresh_from_db(from_queryset=Artwork.objects.select_for_update())
    if not artwork.is_purchasable:
        raise NotAvailable

    expires = timezone.now() + RESERVATION
    order = Order.objects.create(
        artwork=artwork,
        amount_pence=artwork.price_pence,
        delivery_pence=SiteContent.load().delivery_pence,
        expires_at=expires,
    )
    session = stripe_client.create_checkout_session(order, success_url, cancel_url)

    order.stripe_session_id = session.id
    order.save(update_fields=['stripe_session_id'])
    artwork.reserved_until = expires
    artwork.save(update_fields=['reserved_until'])
    assert session.url
    return session.url
