import pytest

from gesso.artworks.models import ArtworkImage
from gesso.enquiries.models import Enquiry
from gesso.web import props
from gesso.web.formatting import dimensions, paragraphs, price

INERTIA = {'X-Inertia': 'true'}


def test_published_artwork_renders(client, make_artwork):
    make_artwork(title='Live', slug='live', is_published=True)

    response = client.get('/work/live', headers=INERTIA)

    assert response.status_code == 200
    assert response.json()['component'] == 'Work/Show'
    assert response.json()['props']['artwork']['title'] == 'Live'


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

    assert props.responsive_image(image) == {
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
    assert props.site_props(path)['nav'][0]['current'] is current


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
