from datetime import timedelta

from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone

from gesso.artworks.models import Artwork
from gesso.commerce import stripe_client
from gesso.commerce.models import Order, StripeEvent
from gesso.content.models import SiteContent
from gesso.web.formatting import price

RESERVATION = timedelta(minutes=31)


class NotAvailable(Exception):
    pass


@transaction.atomic
def start_checkout(artwork: Artwork, success_url: str, cancel_url: str) -> str:
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
    session = stripe_client.create_checkout_session(order, success_url, cancel_url)
    order.stripe_session_id = session.id
    order.save(update_fields=['stripe_session_id'])
    return session.url


@transaction.atomic
def handle_event(event) -> None:
    _, created = StripeEvent.objects.get_or_create(id=event['id'])

    if not created:
        return

    session = event['data']['object']
    orders = Order.objects.select_for_update().select_related('artwork')
    match event['type']:
        case 'checkout.session.completed' if session['payment_status'] == 'paid':
            order = orders.get(stripe_session_id=session['id'])
            buyer = stripe_client.buyer(session)
            order.mark_paid(buyer.name, buyer.email, buyer.address)
            transaction.on_commit(lambda: notify_sale(order), robust=True)
            transaction.on_commit(lambda: confirm_to_buyer(order), robust=True)
        case 'checkout.session.expired':
            orders.get(stripe_session_id=session['id']).mark_expired()


def notify_sale(order: Order) -> None:
    recipient = SiteContent.load().notification_email
    if not recipient:
        return
    EmailMessage(
        subject=f'{order.artwork.title} sold, {price(order.amount_pence + order.delivery_pence)}',
        body=f'{order.buyer_name} <{order.buyer_email}>\n\n{order.shipping_address}',
        to=[recipient],
        reply_to=[order.buyer_email],
    ).send()


def confirm_to_buyer(order: Order) -> None:
    recipient = SiteContent.load().notification_email
    EmailMessage(
        subject=f'Your order: {order.artwork.title}',
        body=(
            f'Thank you for buying {order.artwork.title}.\n\n'
            f'Total paid: {price(order.amount_pence + order.delivery_pence)}, including UK delivery.\n'
            f"We'll be in touch shortly to arrange delivery. Reply to this email with any questions."
        ),
        to=[order.buyer_email],
        reply_to=[recipient] if recipient else None,
    ).send()
