from datetime import timedelta
from itertools import count
from types import SimpleNamespace

import pytest
import stripe
from django.utils import timezone

from gesso.artworks.models import Artwork, ArtworkStatus
from gesso.commerce import stripe_client
from gesso.commerce.models import Order, OrderStatus, StripeEvent
from gesso.commerce.services import NotAvailable, cancel_checkout, handle_event, start_checkout
from gesso.content.models import Page, SiteContent

SITE_URL = 'http://testserver/'


@pytest.fixture
def for_sale(make_artwork):
    return make_artwork(is_published=True, status=ArtworkStatus.AVAILABLE, price_pence=340000)


def test_checkout_reserves_the_work(for_sale, stripe_sessions):
    content = SiteContent.load()
    content.delivery_pence = 8500
    content.save()

    assert start_checkout(for_sale, SITE_URL) == 'https://checkout.stripe.test/pay'

    for_sale.refresh_from_db()
    order = Order.objects.get()
    assert for_sale.is_reserved
    assert for_sale.reserved_until == order.expires_at
    assert (order.amount_pence, order.delivery_pence, order.stripe_session_id) == (340000, 8500, 'cs_test_1')


def test_checkout_refuses_a_reserved_work(for_sale, stripe_sessions):
    start_checkout(for_sale, SITE_URL)

    with pytest.raises(NotAvailable):
        start_checkout(for_sale, SITE_URL)

    assert Order.objects.count() == 1


def test_checkout_takes_over_a_lapsed_reservation(for_sale, stripe_sessions):
    Artwork.objects.filter(pk=for_sale.pk).update(reserved_until=timezone.now() - timedelta(minutes=1))

    start_checkout(for_sale, SITE_URL)

    assert len(stripe_sessions) == 1


def test_stripe_failure_leaves_the_work_unreserved(for_sale, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError('Stripe is down')

    monkeypatch.setattr(stripe_client, 'create_checkout_session', fail)

    with pytest.raises(RuntimeError):
        start_checkout(for_sale, SITE_URL)

    for_sale.refresh_from_db()
    assert for_sale.is_purchasable
    assert not Order.objects.exists()


_events = count(1)


def _checkout(artwork) -> Order:
    start_checkout(artwork, SITE_URL)
    return Order.objects.latest('created_at')


def _event(type, order, **session):
    session = {
        'id': order.stripe_session_id,
        'payment_status': 'paid',
        'customer_details': {'name': 'B', 'email': 'b@example.com'},
        'collected_information': {
            'shipping_details': {
                'name': 'B',
                'address': {
                    'line1': '1 Quay St',
                    'line2': None,
                    'city': 'Dover',
                    'state': None,
                    'postal_code': 'CT16 1AA',
                    'country': 'GB',
                },
            }
        },
    } | session
    return {'id': f'evt_{next(_events)}', 'type': type, 'data': {'object': session}}


def test_completed_sells_the_work_and_sends_emails(for_sale, stripe_sessions, mailoutbox, django_capture_on_commit_callbacks):
    content = SiteContent.load()
    content.notification_email = 'studio@example.com'
    content.save()
    order = _checkout(for_sale)

    with django_capture_on_commit_callbacks(execute=True):
        handle_event(_event('checkout.session.completed', order))

    for_sale.refresh_from_db()
    order.refresh_from_db()
    assert (for_sale.status, for_sale.reserved_until) == (ArtworkStatus.SOLD, None)
    assert order.status == OrderStatus.PAID
    assert order.shipping_address == 'B\n1 Quay St\nDover\nCT16 1AA\nGB'
    assert sorted(m.to[0] for m in mailoutbox) == ['b@example.com', 'studio@example.com']


def test_replayed_event_is_a_no_op(for_sale, stripe_sessions, mailoutbox, django_capture_on_commit_callbacks):
    event = _event('checkout.session.completed', _checkout(for_sale))

    with django_capture_on_commit_callbacks(execute=True):
        handle_event(event)
        handle_event(event)

    assert [m.to for m in mailoutbox] == [['b@example.com']]


def test_expired_frees_the_work(for_sale, stripe_sessions):
    order = _checkout(for_sale)

    handle_event(_event('checkout.session.expired', order))

    for_sale.refresh_from_db()
    order.refresh_from_db()
    assert for_sale.is_purchasable
    assert order.status == OrderStatus.EXPIRED


def test_manual_status_survives_expiry(for_sale, stripe_sessions):
    order = _checkout(for_sale)
    Artwork.objects.filter(pk=for_sale.pk).update(status=ArtworkStatus.NOT_FOR_SALE)

    handle_event(_event('checkout.session.expired', order))

    for_sale.refresh_from_db()
    assert for_sale.status == ArtworkStatus.NOT_FOR_SALE


def test_old_expiry_leaves_a_newer_reservation_alone(for_sale, stripe_sessions):
    first = _checkout(for_sale)
    Artwork.objects.filter(pk=for_sale.pk).update(reserved_until=timezone.now() - timedelta(minutes=1))
    _checkout(for_sale)

    handle_event(_event('checkout.session.expired', first))

    for_sale.refresh_from_db()
    assert for_sale.is_reserved


def test_stripe_webhook_rejects_bad_signature(client, settings):
    settings.STRIPE_WEBHOOK_SECRET = 'whsec_test'

    response = client.post('/webhooks/stripe', '{}', content_type='application/json', headers={'Stripe-Signature': 't=1,v1=bad'})

    assert response.status_code == 400


def _paid(artwork) -> Order:
    order = _checkout(artwork)
    handle_event(_event('checkout.session.completed', order))
    order.refresh_from_db()
    return order


def test_admin_ship_button_marks_a_paid_order_shipped(admin_client, for_sale, stripe_sessions):
    order = _paid(for_sale)

    page = admin_client.get(f'/admin/commerce/order/{order.pk}/change/').content.decode()
    response = admin_client.get(f'/admin/commerce/order/{order.pk}/ship/')

    order.refresh_from_db()
    assert 'Mark shipped' in page
    assert '1 Quay St<br>Dover' in page
    assert response.status_code == 302
    assert order.status == OrderStatus.SHIPPED
    assert order.shipped_at is not None


def test_admin_ship_button_is_refused_for_an_unpaid_order(admin_client, for_sale, stripe_sessions):
    order = _checkout(for_sale)

    response = admin_client.get(f'/admin/commerce/order/{order.pk}/ship/')

    order.refresh_from_db()
    assert response.status_code == 403
    assert order.status == OrderStatus.PENDING


def test_checkout_sends_stripe_our_success_and_cancel_urls(for_sale, stripe_sessions):
    start_checkout(for_sale, SITE_URL)

    order = Order.objects.get()
    assert stripe_sessions[0]['success_url'] == 'http://testserver/checkout/success'
    assert stripe_sessions[0]['cancel_url'] == f'http://testserver/checkout/cancel/{order.pk}'


def test_cancel_frees_the_work_at_once(for_sale, stripe_sessions, monkeypatch):
    monkeypatch.setattr(stripe_client, 'expire_session', lambda session_id: True)
    order = _checkout(for_sale)

    assert cancel_checkout(order.pk) == for_sale

    for_sale.refresh_from_db()
    order.refresh_from_db()
    assert for_sale.is_purchasable
    assert order.status == OrderStatus.EXPIRED


def test_cancel_after_payment_changes_nothing(for_sale, stripe_sessions, monkeypatch):
    monkeypatch.setattr(stripe_client, 'expire_session', lambda session_id: False)
    order = _checkout(for_sale)

    cancel_checkout(order.pk)

    for_sale.refresh_from_db()
    order.refresh_from_db()
    assert for_sale.is_reserved
    assert order.status == OrderStatus.PENDING


def test_cancel_view_returns_the_buyer_to_the_work(client, for_sale, stripe_sessions, monkeypatch):
    monkeypatch.setattr(stripe_client, 'expire_session', lambda session_id: True)
    order = _checkout(for_sale)

    response = client.get(f'/checkout/cancel/{order.pk}')

    assert response.status_code == 302
    assert response['Location'] == f'/work/{for_sale.slug}'


def test_events_for_sessions_from_elsewhere_are_ignored(db):
    event = {
        'id': 'evt_elsewhere',
        'type': 'checkout.session.expired',
        'data': {'object': {'id': 'cs_test_not_ours', 'payment_status': 'unpaid'}},
    }

    handle_event(event)

    assert StripeEvent.objects.filter(id='evt_elsewhere').exists()


def test_checkout_links_the_terms_and_returns_pages(for_sale, stripe_sessions):
    start_checkout(for_sale, SITE_URL)

    assert stripe_sessions[0]['note'] == (
        'By paying you agree to our [terms of sale](http://testserver/pages/terms)'
        ' and [delivery & returns](http://testserver/pages/delivery-and-returns).'
    )


def test_checkout_has_no_note_without_the_pages(for_sale, stripe_sessions):
    Page.objects.all().delete()

    start_checkout(for_sale, SITE_URL)

    assert stripe_sessions[0]['note'] == ''


@pytest.mark.parametrize(('note', 'custom_text'), [('Read the terms.', {'submit': {'message': 'Read the terms.'}}), ('', None)])
def test_stripe_shows_the_note_above_the_pay_button(for_sale, monkeypatch, note, custom_text):
    sent = []

    def create(params, options):
        sent.append(params)
        return SimpleNamespace(id='cs_test_1', url='https://checkout.stripe.test/pay')

    client = SimpleNamespace(v1=SimpleNamespace(checkout=SimpleNamespace(sessions=SimpleNamespace(create=create))))
    monkeypatch.setattr(stripe, 'StripeClient', lambda key: client)
    order = Order.objects.create(artwork=for_sale, amount_pence=340000, delivery_pence=0, expires_at=timezone.now())

    stripe_client.create_checkout_session(order, 'https://site/ok', 'https://site/cancel', note=note)

    assert sent[0].get('custom_text') == custom_text
