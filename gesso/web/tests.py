import pytest

from gesso.artworks.models import Artwork, ArtworkImage

from . import props

INERTIA = {'X-Inertia': 'true'}


@pytest.mark.django_db
def test_published_artwork_renders(client):
    Artwork.objects.create(title='Live', slug='live', year=2024, is_published=True)

    response = client.get('/work/live', headers=INERTIA)

    assert response.status_code == 200
    assert response.json()['component'] == 'Work/Show'
    assert response.json()['props']['artwork'] == {'title': 'Live', 'year': 2024, 'cover': None}


@pytest.mark.django_db
def test_draft_artwork_404s(client):
    Artwork.objects.create(title='Draft', slug='draft', year=2024)

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
