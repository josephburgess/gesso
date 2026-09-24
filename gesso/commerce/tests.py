from datetime import timedelta

import pytest
from django.utils import timezone

from gesso.artworks.models import Artwork, ArtworkStatus
from gesso.commerce import stripe_client
from gesso.commerce.models import Order
from gesso.commerce.services import NotAvailable, start_checkout
from gesso.content.models import SiteContent

SUCCESS_URL = 'http://testserver/checkout/success'
CANCEL_URL = 'http://testserver/work/a'


@pytest.fixture
def for_sale(make_artwork):
    return make_artwork(is_published=True, status=ArtworkStatus.AVAILABLE, price_pence=340000)


def test_checkout_reserves_the_work(for_sale, stripe_sessions):
    content = SiteContent.load()
    content.delivery_pence = 8500
    content.save()

    assert start_checkout(for_sale, SUCCESS_URL, CANCEL_URL) == 'https://checkout.stripe.test/pay'

    for_sale.refresh_from_db()
    order = Order.objects.get()
    assert for_sale.is_reserved
    assert for_sale.reserved_until == order.expires_at
    assert (order.amount_pence, order.delivery_pence, order.stripe_session_id) == (340000, 8500, 'cs_test_1')


def test_checkout_refuses_a_reserved_work(for_sale, stripe_sessions):
    start_checkout(for_sale, SUCCESS_URL, CANCEL_URL)

    with pytest.raises(NotAvailable):
        start_checkout(for_sale, SUCCESS_URL, CANCEL_URL)

    assert Order.objects.count() == 1


def test_checkout_takes_over_a_lapsed_reservation(for_sale, stripe_sessions):
    Artwork.objects.filter(pk=for_sale.pk).update(reserved_until=timezone.now() - timedelta(minutes=1))

    start_checkout(for_sale, SUCCESS_URL, CANCEL_URL)

    assert len(stripe_sessions) == 1


def test_stripe_failure_leaves_the_work_unreserved(for_sale, monkeypatch):
    def fail(*args):
        raise RuntimeError('Stripe is down')

    monkeypatch.setattr(stripe_client, 'create_checkout_session', fail)

    with pytest.raises(RuntimeError):
        start_checkout(for_sale, SUCCESS_URL, CANCEL_URL)

    for_sale.refresh_from_db()
    assert for_sale.is_purchasable
    assert not Order.objects.exists()
