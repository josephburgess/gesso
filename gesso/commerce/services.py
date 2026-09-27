from datetime import timedelta
from urllib.parse import urljoin

from django.core.mail import EmailMessage
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from gesso.artworks.models import Artwork
from gesso.commerce import stripe_client
from gesso.commerce.models import Order, OrderStatus, StripeEvent
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
    EmailMessage(
        subject=f'{order.artwork.title} sold, {price(order.total_pence)}',
        body=f'{order.buyer_name} <{order.buyer_email}>\n\n{order.shipping_address}',
        to=[recipient],
        reply_to=[order.buyer_email],
    ).send()


def send_shipped(order: Order) -> None:
    recipient = SiteContent.load().notification_email
    courier = f' with {order.courier}' if order.courier else ''
    tracking = f'\n\nTrack it here: {order.tracking_url}' if order.tracking_url else ''
    EmailMessage(
        subject=f'{order.artwork.title} is on its way',
        body=f'{order.artwork.title} has been sent{courier}.{tracking}\n\nReply to this email with any questions.',
        to=[order.buyer_email],
        reply_to=[recipient] if recipient else None,
    ).send()


def confirm_to_buyer(order: Order) -> None:
    recipient = SiteContent.load().notification_email
    EmailMessage(
        subject=f'Your order: {order.artwork.title}',
        body=(
            f'Thank you for buying {order.artwork.title}.\n\n'
            f'Total paid: {price(order.total_pence)}, including UK delivery.\n'
            f"We'll be in touch shortly to arrange delivery. Reply to this email with any questions."
        ),
        to=[order.buyer_email],
        reply_to=[recipient] if recipient else None,
    ).send()
