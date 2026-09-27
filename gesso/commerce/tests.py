from datetime import timedelta
from itertools import count
from types import SimpleNamespace

import pytest
import stripe
from django.utils import timezone

from gesso.artworks.models import Artwork, ArtworkStatus
from gesso.commerce import stripe_client
from gesso.commerce.models import Order, OrderStatus, StripeEvent
from gesso.commerce.services import NotAvailable, cancel_checkout, handle_event, send_shipped, start_checkout
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


def test_admin_ship_button_asks_for_tracking_first(admin_client, for_sale, stripe_sessions):
    order = _paid(for_sale)

    page = admin_client.get(f'/admin/commerce/order/{order.pk}/change/').content.decode()
    form = admin_client.get(f'/admin/commerce/order/{order.pk}/ship/')

    order.refresh_from_db()
    assert 'Mark shipped' in page
    assert '1 Quay St<br>Dover' in page
    assert 'Tracking link' in form.content.decode()
    assert order.status == OrderStatus.PAID


def test_admin_ship_records_tracking_and_emails_the_buyer(admin_client, for_sale, stripe_sessions, mailoutbox):
    order = _paid(for_sale)
    data = {'courier': 'Artsy Couriers', 'tracking_url': 'https://track.example/123', 'notify': 'on'}

    response = admin_client.post(f'/admin/commerce/order/{order.pk}/ship/', data)

    order.refresh_from_db()
    assert response.status_code == 302
    assert (order.status, order.courier, order.tracking_url) == (OrderStatus.SHIPPED, 'Artsy Couriers', 'https://track.example/123')
    assert order.shipped_at is not None
    assert [(m.to, m.subject) for m in mailoutbox] == [(['b@example.com'], f'{for_sale.title} is on its way')]
    assert 'with Artsy Couriers' in mailoutbox[0].body
    assert 'https://track.example/123' in mailoutbox[0].body


def test_admin_ship_can_skip_the_email(admin_client, for_sale, stripe_sessions, mailoutbox):
    order = _paid(for_sale)

    admin_client.post(f'/admin/commerce/order/{order.pk}/ship/', {'courier': '', 'tracking_url': ''})

    order.refresh_from_db()
    assert order.status == OrderStatus.SHIPPED
    assert mailoutbox == []


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


def test_admin_full_refund_marks_the_order_refunded_and_can_relist(admin_client, for_sale, stripe_sessions):
    order = _paid(for_sale)

    form = admin_client.get(f'/admin/commerce/order/{order.pk}/refund/').content.decode()
    response = admin_client.post(f'/admin/commerce/order/{order.pk}/refund/', {'amount': '3400.00', 'relist': 'on'})

    order.refresh_from_db()
    for_sale.refresh_from_db()
    assert 'value="3400"' in form
    assert response.status_code == 302
    assert (order.status, order.refund_pence) == (OrderStatus.REFUNDED, 340000)
    assert order.refunded_at is not None
    assert for_sale.status == ArtworkStatus.AVAILABLE


def test_partial_refund_keeps_the_order_and_the_sale(for_sale, stripe_sessions):
    order = _paid(for_sale)

    order.record_refund(5000, relist=False)

    for_sale.refresh_from_db()
    assert (order.status, order.refund_pence) == (OrderStatus.PAID, 5000)
    assert for_sale.status == ArtworkStatus.SOLD


def test_refund_cannot_exceed_what_was_paid(admin_client, for_sale, stripe_sessions):
    order = _paid(for_sale)

    response = admin_client.post(f'/admin/commerce/order/{order.pk}/refund/', {'amount': '9999.00'})

    order.refresh_from_db()
    assert 'more than the buyer paid' in response.content.decode()
    assert order.refunded_at is None


def test_refund_is_refused_for_an_unpaid_order(admin_client, for_sale, stripe_sessions):
    order = _checkout(for_sale)

    assert admin_client.get(f'/admin/commerce/order/{order.pk}/refund/').status_code == 403


def test_admin_records_an_exhibition_sale(admin_client, for_sale):
    data = {
        'price': '3200',
        'sold_on': '2026-09-20',
        'source': 'exhibition',
        'venue': 'Bermondsey Open',
        'buyer_name': 'C Collector',
        'buyer_email': '',
        'notes': 'Paid by bank transfer',
    }

    form = admin_client.get(f'/admin/artworks/artwork/{for_sale.pk}/record-sale/').content.decode()
    response = admin_client.post(f'/admin/artworks/artwork/{for_sale.pk}/record-sale/', data)

    order = Order.objects.get()
    for_sale.refresh_from_db()
    assert 'value="3400"' in form
    assert response['Location'] == f'/admin/commerce/order/{order.pk}/change/'
    assert (order.source, order.venue, order.amount_pence, order.buyer_name) == ('exhibition', 'Bermondsey Open', 320000, 'C Collector')
    assert order.status == OrderStatus.SHIPPED
    assert timezone.localdate(order.paid_at).isoformat() == '2026-09-20'
    assert for_sale.status == ArtworkStatus.SOLD


def test_sale_still_to_deliver_goes_to_orders_to_ship(admin_client, for_sale):
    data = {'price': '3400', 'sold_on': '2026-09-20', 'source': 'private', 'to_deliver': 'on'}

    admin_client.post(f'/admin/artworks/artwork/{for_sale.pk}/record-sale/', data)

    assert list(Order.objects.to_ship()) == [Order.objects.get(source='private')]


def test_sold_work_has_no_record_sale_button(admin_client, make_artwork):
    sold = make_artwork(status=ArtworkStatus.SOLD)

    assert admin_client.get(f'/admin/artworks/artwork/{sold.pk}/record-sale/').status_code == 403


def test_order_notes_are_editable(admin_client, for_sale, stripe_sessions):
    order = _paid(for_sale)

    admin_client.post(f'/admin/commerce/order/{order.pk}/change/', {'notes': 'Wrapped twice'})

    order.refresh_from_db()
    assert order.notes == 'Wrapped twice'


def test_emails_come_from_the_site_name(for_sale, stripe_sessions, mailoutbox, settings):
    settings.DEFAULT_FROM_EMAIL = 'Gesso <studio@example.com>'
    content = SiteContent.load()
    content.site_name = 'Elise Beer'
    content.save()
    order = _paid(for_sale)

    send_shipped(order)

    assert mailoutbox[0].from_email == 'Elise Beer <studio@example.com>'
