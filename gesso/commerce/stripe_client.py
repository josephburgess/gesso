from typing import NamedTuple

import stripe
from django.conf import settings

from gesso.commerce.models import Order


class CheckoutSession(NamedTuple):
    id: str
    url: str


def create_checkout_session(order: Order, success_url: str, cancel_url: str) -> CheckoutSession:
    client = stripe.StripeClient(settings.STRIPE_SECRET_KEY)
    session = client.v1.checkout.sessions.create(
        {
            'mode': 'payment',
            'line_items': [
                {
                    'quantity': 1,
                    'price_data': {
                        'currency': 'gbp',
                        'unit_amount': order.amount_pence,
                        'product_data': {'name': order.artwork.title},
                    },
                }
            ],
            'shipping_address_collection': {'allowed_countries': ['GB']},
            'shipping_options': [
                {
                    'shipping_rate_data': {
                        'type': 'fixed_amount',
                        'display_name': 'UK delivery',
                        'fixed_amount': {'amount': order.delivery_pence, 'currency': 'gbp'},
                    }
                }
            ],
            'client_reference_id': str(order.pk),
            'success_url': success_url + '?session_id={CHECKOUT_SESSION_ID}',
            'cancel_url': cancel_url,
            'expires_at': int(order.expires_at.timestamp()),
        },
        {'idempotency_key': str(order.pk)},
    )
    if session.url is None:
        raise RuntimeError(f'Stripe returned checkout session {session.id} without a URL')
    return CheckoutSession(session.id, session.url)


def construct_event(payload: bytes, signature: str) -> stripe.Event | None:
    try:
        return stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError, stripe.SignatureVerificationError:
        return None
