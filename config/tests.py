from datetime import timedelta

from django.utils import timezone

from config.dashboard import orders_to_ship, unread_enquiries
from gesso.artworks.models import ArtworkImage
from gesso.commerce.models import Order, OrderSource, OrderStatus
from gesso.enquiries.models import Enquiry
from gesso.stats.models import DailyReferrer, DailyView


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


def test_sales_this_year_count_offline_sales_and_refunds(admin_client, make_artwork):
    _paid_order(make_artwork())
    refunded = _paid_order(make_artwork())
    refunded.record_refund(8500, relist=False)
    Order.objects.create(
        artwork=make_artwork(),
        status=OrderStatus.SHIPPED,
        source=OrderSource.EXHIBITION,
        amount_pence=120000,
        delivery_pence=0,
        paid_at=timezone.now(),
    )
    Order.objects.create(
        artwork=make_artwork(), status=OrderStatus.PAID, amount_pence=99900, delivery_pence=0, paid_at=timezone.now() - timedelta(days=400)
    )
    Order.objects.create(artwork=make_artwork(), status=OrderStatus.EXPIRED, amount_pence=99900, delivery_pence=0)

    html = admin_client.get('/admin/').content.decode()

    assert '£8,085' in html


def test_dashboard_shows_views_and_where_they_came_from(admin_client, make_artwork):
    today = timezone.localdate()
    artwork = make_artwork(title='Harbour at Dusk', slug='harbour')
    DailyView.objects.create(day=today, path='/work/harbour', artwork=artwork, views=12)
    DailyView.objects.create(day=today - timedelta(days=1), path='/', views=30)
    DailyView.objects.create(day=today - timedelta(days=45), path='/', views=21)
    DailyReferrer.objects.create(day=today, host='instagram.com', visits=5)

    html = admin_client.get('/admin/').content.decode()
    works = html.split('Most viewed works')[1]

    assert '>42<' in html.replace(' ', '').replace('\n', '')
    assert '+100% on the 30 days before' in html
    assert 'data-type="line"' in html
    assert 'Harbour at Dusk' in works
    assert 'instagram.com' in html
