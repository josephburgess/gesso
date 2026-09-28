from datetime import date, datetime, time, timedelta
from urllib.parse import urljoin

from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from gesso.artworks.models import Artwork
from gesso.commerce import stripe_client
from gesso.commerce.models import Order, OrderSource, OrderStatus, StripeEvent
from gesso.content.mail import send_templated
from gesso.content.models import Page, SiteContent
from gesso.web.formatting import price

RESERVATION = timedelta(minutes=31)


class NotAvailable(Exception):
    pass


@transaction.atomic
def start_checkout(artwork: Artwork, site_url: str) -> str:
    artwork.refresh_from_db(from_queryset=Artwork.objects.select_for_update())
    if not artwork.is_purchasable:
        raise NotAvailable

    expires = timezone.now() + RESERVATION
    artwork.reserve(until=expires)
    order = Order.objects.create(
        artwork=artwork,
        amount_pence=artwork.price_pence,
        delivery_pence=SiteContent.load().delivery_pence,
        expires_at=expires,
    )
    session = stripe_client.create_checkout_session(
        order,
        success_url=urljoin(site_url, reverse('checkout_success')),
        cancel_url=urljoin(site_url, reverse('checkout_cancel', args=[order.pk])),
        note=_policy_note(site_url),
    )
    order.stripe_session_id = session.id
    order.save(update_fields=['stripe_session_id'])
    return session.url


@transaction.atomic
def record_sale(
    artwork: Artwork,
    *,
    price_pence: int,
    sold_on: date,
    source: OrderSource,
    venue: str,
    buyer_name: str,
    buyer_email: str,
    notes: str,
    to_deliver: bool,
) -> Order:
    paid_at = timezone.make_aware(datetime.combine(sold_on, time(12)))
    order = Order.objects.create(
        artwork=artwork,
        source=source,
        venue=venue,
        status=OrderStatus.PAID if to_deliver else OrderStatus.SHIPPED,
        amount_pence=price_pence,
        delivery_pence=0,
        buyer_name=buyer_name,
        buyer_email=buyer_email,
        notes=notes,
        paid_at=paid_at,
        shipped_at=None if to_deliver else paid_at,
    )
    artwork.mark_sold()
    return order


def _policy_note(site_url: str) -> str:
    pages = Page.objects.filter(slug__in=(Page.TERMS, Page.RETURNS)).order_by('position')
    links = [f'[{page.title.lower()}]({urljoin(site_url, page.get_absolute_url())})' for page in pages]
    return f'By paying you agree to our {" and ".join(links)}.' if links else ''


@transaction.atomic
def cancel_checkout(order_id) -> Artwork | None:
    order = Order.objects.select_for_update().select_related('artwork').filter(pk=order_id).first()
    if order is None:
        return None
    if order.status == OrderStatus.PENDING and order.stripe_session_id and stripe_client.expire_session(order.stripe_session_id):
        order.mark_expired()
    return order.artwork


@transaction.atomic
def handle_event(event) -> None:
    _, created = StripeEvent.objects.get_or_create(id=event['id'])

    if not created:
        return

    session = event['data']['object']
    order = Order.objects.select_for_update().select_related('artwork').filter(stripe_session_id=session['id']).first()
    if order is None:
        return

    match event['type']:
        case 'checkout.session.completed' if session['payment_status'] == 'paid':
            buyer = stripe_client.buyer(session)
            order.mark_paid(buyer.name, buyer.email, buyer.address)
            transaction.on_commit(lambda: notify_sale(order), robust=True)
            transaction.on_commit(lambda: confirm_to_buyer(order), robust=True)
        case 'checkout.session.expired':
            order.mark_expired()


def notify_sale(order: Order) -> None:
    recipient = SiteContent.load().notification_email
    if not recipient:
        return
    send_templated('sale_alert', {'order': order, 'total': price(order.total_pence)}, to=[recipient], reply_to=[order.buyer_email])


def send_shipped(order: Order) -> None:
    recipient = SiteContent.load().notification_email
    send_templated('shipped', {'order': order}, to=[order.buyer_email], reply_to=[recipient] if recipient else None)


def confirm_to_buyer(order: Order) -> None:
    recipient = SiteContent.load().notification_email
    send_templated(
        'order_confirmation',
        {'order': order, 'total': price(order.total_pence)},
        to=[order.buyer_email],
        reply_to=[recipient] if recipient else None,
    )
