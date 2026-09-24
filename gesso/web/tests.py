from datetime import timedelta

import pytest
from django.utils import timezone

from gesso.artworks.models import ArtworkImage, ArtworkStatus
from gesso.content.models import SiteContent
from gesso.enquiries.models import Enquiry
from gesso.web.formatting import dimensions, paragraphs, price
from gesso.web.middleware import site_props
from gesso.web.views.work import responsive_image

INERTIA = {'X-Inertia': 'true'}


def test_published_artwork_renders(client, make_artwork):
    make_artwork(title='Live', slug='live', is_published=True)

    response = client.get('/work/live', headers=INERTIA)

    assert response.status_code == 200
    assert response.json()['component'] == 'Work/Show'
    assert response.json()['props']['artwork']['title'] == 'Live'


def test_artwork_page_offers_an_enquiry(client, make_artwork):
    make_artwork(slug='live', is_published=True)

    purchase = client.get('/work/live', headers=INERTIA).json()['props']['purchase']

    assert purchase == {'enquire_href': '/contact?artwork=live', 'enquire_label': 'Enquire about this work', 'action': None, 'note': ''}


def test_reserved_artwork_keeps_its_price(client, make_artwork):
    make_artwork(
        slug='held',
        is_published=True,
        status=ArtworkStatus.AVAILABLE,
        price_pence=340000,
        reserved_until=timezone.now() + timedelta(minutes=5),
    )

    artwork = client.get('/work/held', headers=INERTIA).json()['props']['artwork']

    assert (artwork['status'], artwork['price']) == ('Reserved', '£3,400')


def test_available_artwork_can_be_purchased(client, make_artwork):
    content = SiteContent.load()
    content.delivery_pence = 8500
    content.save()
    make_artwork(slug='a', is_published=True, status=ArtworkStatus.AVAILABLE, price_pence=100)

    purchase = client.get('/work/a', headers=INERTIA).json()['props']['purchase']

    assert purchase['action'] == '/work/a/checkout'
    assert 'Plus £85 UK delivery.' in purchase['note']


def test_sold_artwork_offers_similar_work(client, make_artwork):
    make_artwork(slug='gone', is_published=True, status=ArtworkStatus.SOLD)

    purchase = client.get('/work/gone', headers=INERTIA).json()['props']['purchase']

    assert (purchase['action'], purchase['enquire_label']) == (None, 'Enquire about similar work')


def test_draft_artwork_404s(client, make_artwork):
    make_artwork(slug='draft')

    assert client.get('/work/draft', headers=INERTIA).status_code == 404


def test_responsive_image():
    image = ArtworkImage(
        variants=[
            {'width': 480, 'height': 240, 'name': 'variants/1/480.webp'},
            {'width': 960, 'height': 480, 'name': 'variants/1/960.webp'},
        ]
    )

    assert responsive_image(image) == {
        'src': '/media/variants/1/960.webp',
        'srcset': '/media/variants/1/480.webp 480w, /media/variants/1/960.webp 960w',
        'width': 960,
        'height': 480,
    }


@pytest.mark.parametrize(
    ('path', 'current'),
    [('/work', True), ('/work/some-painting', True), ('/workshop', False), ('/', False)],
)
def test_work_nav_current(path, current):
    assert site_props(path)['nav'][0]['current'] is current


@pytest.mark.parametrize(
    ('height', 'width', 'expected'),
    [(700, 500, '70 × 50 cm'), (705, 500, '70.5 × 50 cm')],
)
def test_dimensions(height, width, expected):
    assert dimensions(height, width) == expected


@pytest.mark.parametrize(('pence', 'expected'), [(340000, '£3,400'), (340050, '£3,400.50')])
def test_price(pence, expected):
    assert price(pence) == expected


def test_paragraphs():
    assert paragraphs('One.\r\n\r\nTwo\nlines.\n  \nThree.') == ['One.', 'Two\nlines.', 'Three.']


def test_about_renders(client, db):
    response = client.get('/about', headers=INERTIA)

    assert response.status_code == 200
    assert response.json()['component'] == 'About'


def test_contact_post_saves_enquiry(client, db):
    data = {'name': 'A', 'email': 'a@example.com', 'message': 'Hi'}

    response = client.post('/contact', data, content_type='application/json', headers=INERTIA)

    assert response.status_code == 302
    assert Enquiry.objects.get().name == 'A'


def test_contact_post_returns_errors(client, db):
    data = {'name': '', 'email': 'nope', 'message': ''}

    response = client.post('/contact', data, content_type='application/json', headers=INERTIA)

    assert response.status_code == 200
    assert response.json()['props']['errors'].keys() == {'name', 'email', 'message'}
    assert not Enquiry.objects.exists()


def test_contact_spam_catcher_pretends_success(client, db):
    data = {'name': 'A', 'email': 'a@example.com', 'message': 'Hi', 'website': 'spam.example'}

    response = client.post('/contact', data, content_type='application/json', headers=INERTIA)

    assert response.status_code == 302
    assert not Enquiry.objects.exists()


def test_contact_rejects_non_json(client, db):
    assert client.post('/contact', {'name': 'A'}).status_code == 400


def test_home_features_published_works_in_order(client, make_artwork):
    make_artwork(title='Second', is_published=True, featured_order=2)
    make_artwork(title='First', is_published=True, featured_order=1)
    make_artwork(title='Draft', featured_order=3)

    home = client.get('/', headers=INERTIA).json()['props']['home']

    assert [t['title'] for t in home['featured']] == ['First', 'Second']
    assert len(home['index']) == 2


def test_contact_prefills_artwork_from_query(client, make_artwork):
    make_artwork(title='Ferry Light', slug='ferry-light', is_published=True)

    contact = client.get('/contact?artwork=ferry-light', headers=INERTIA).json()['props']['contact']

    assert contact['artwork'] == {'title': 'Ferry Light', 'slug': 'ferry-light'}


def test_contact_links_enquiry_to_artwork(client, make_artwork):
    artwork = make_artwork(slug='ferry-light', is_published=True)
    data = {'name': 'A', 'email': 'a@example.com', 'message': 'Hi', 'artwork': 'ferry-light'}

    client.post('/contact', data, content_type='application/json', headers=INERTIA)

    assert Enquiry.objects.get().artwork == artwork


def test_checkout_sends_the_browser_to_stripe(client, make_artwork, stripe_sessions):
    make_artwork(slug='a', is_published=True, status=ArtworkStatus.AVAILABLE, price_pence=100)

    response = client.post('/work/a/checkout', headers=INERTIA)

    assert response.status_code == 409
    assert response.headers['X-Inertia-Location'] == 'https://checkout.stripe.test/pay'


def test_checkout_of_sold_work_goes_back_to_the_page(client, make_artwork, stripe_sessions):
    make_artwork(slug='a', is_published=True, status=ArtworkStatus.SOLD, price_pence=100)

    response = client.post('/work/a/checkout', headers=INERTIA)

    assert response.status_code == 302
    assert stripe_sessions == []
