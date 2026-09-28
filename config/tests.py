from datetime import timedelta

from django.utils import timezone

from config.dashboard import orders_to_ship, unread_enquiries
from gesso.artworks.models import ArtworkImage
from gesso.commerce.models import Order, OrderStatus
from gesso.enquiries.models import Enquiry


def _paid_order(artwork) -> Order:
    return Order.objects.create(
        artwork=artwork,
        status=OrderStatus.PAID,
        amount_pence=340000,
        delivery_pence=8500,
        buyer_name='B Buyer',
        expires_at=timezone.now() + timedelta(minutes=31),
        paid_at=timezone.now(),
    )


def test_dashboard_shows_what_needs_attention(admin_client, make_artwork):
    sold = make_artwork(title='Ferry Light', featured_order=1)
    _paid_order(sold)
    Enquiry.objects.create(name='Ann Enquirer', email='a@example.com', message='Hi', artwork=sold)

    html = admin_client.get('/admin/').content.decode()

    assert 'Ferry Light' in html
    assert 'B Buyer' in html
    assert '£3,485' in html
    assert 'Ann Enquirer' in html
    assert 'Hero' in html
    assert 'Works without images' in html


def test_badges_only_count_what_needs_doing(rf, make_artwork):
    artwork = make_artwork()
    assert (orders_to_ship(rf.get('/')), unread_enquiries(rf.get('/'))) == (None, None)

    _paid_order(artwork)
    Enquiry.objects.create(name='A', email='a@example.com', message='Hi')

    assert (orders_to_ship(rf.get('/')), unread_enquiries(rf.get('/'))) == (1, 1)


def test_sidebar_uses_studio_names(admin_client, db):
    html = admin_client.get('/admin/').content.decode()

    assert all(label in html for label in ('Works', 'Orders', 'Enquiries', 'Site text'))


def test_admin_uses_the_palette_favicon(client, db):
    html = client.get('/admin/login/').content.decode()

    assert '/static/web/admin-icon.svg' in html
    assert '/static/web/favicon.ico' not in html


def test_dashboard_lists_works_with_photos_missing_alt_text(admin_client, make_artwork):
    described = make_artwork(title='Described')
    ArtworkImage.objects.create(artwork=described, original='originals/a.png', alt='Boats')
    missing = make_artwork(title='Undescribed')
    ArtworkImage.objects.create(artwork=missing, original='originals/b.png', alt='Boats')
    ArtworkImage.objects.create(artwork=missing, original='originals/c.png')

    html = admin_client.get('/admin/').content.decode()
    card = html.split('Photos without alt text')[1]

    assert 'Undescribed' in card
    assert 'Described<' not in card
