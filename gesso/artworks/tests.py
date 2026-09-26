import io
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from gesso.artworks import processing
from gesso.artworks.admin import ArtworkAdminForm
from gesso.artworks.models import Artwork, ArtworkImage, ArtworkStatus


def _png(width, height):
    buffer = io.BytesIO()
    Image.new('RGB', (width, height)).save(buffer, 'PNG')
    buffer.seek(0)
    return buffer


def test_published_excludes_drafts(make_artwork):
    live = make_artwork(slug='live', is_published=True)
    make_artwork(slug='draft')

    assert list(Artwork.objects.published()) == [live]


def test_variants_never_upscale():
    variants = processing.webp_variants(_png(1000, 500))

    assert [(v.width, v.height) for v in variants] == [(480, 240), (960, 480), (1000, 500)]


FORM_DATA = {
    'title': 'A',
    'slug': 'a',
    'year': 2024,
    'medium': 'Oil',
    'status': 'available',
    'height_cm': '70.5',
    'width_cm': '50',
    'price': '3400.50',
}


def test_admin_form_converts_units(db):
    form = ArtworkAdminForm(FORM_DATA)
    assert form.is_valid(), form.errors

    artwork = form.save()

    assert (artwork.height_mm, artwork.width_mm, artwork.price_pence) == (705, 500, 340050)


def test_admin_form_needs_price_when_available(db):
    form = ArtworkAdminForm(FORM_DATA | {'price': ''})

    assert 'price' in form.errors


def test_reservation_holds_until_it_lapses(make_artwork):
    held = make_artwork(status=ArtworkStatus.AVAILABLE, price_pence=100, reserved_until=timezone.now() + timedelta(minutes=5))
    lapsed = make_artwork(status=ArtworkStatus.AVAILABLE, price_pence=100, reserved_until=timezone.now() - timedelta(minutes=5))

    assert (held.is_purchasable, held.display_status) == (False, 'Reserved')
    assert (lapsed.is_purchasable, lapsed.display_status) == (True, 'Available')


def test_sold_work_is_not_shown_as_reserved(make_artwork):
    artwork = make_artwork(status=ArtworkStatus.SOLD, reserved_until=timezone.now() + timedelta(minutes=5))

    assert artwork.display_status == 'Sold'


def test_cover_url_is_the_largest_variant_of_the_first_image(make_artwork):
    artwork = make_artwork()
    ArtworkImage.objects.create(
        artwork=artwork,
        original='originals/a.jpg',
        variants=[
            {'width': 480, 'height': 360, 'name': 'variants/1/480.webp'},
            {'width': 960, 'height': 720, 'name': 'variants/1/960.webp'},
        ],
    )

    assert artwork.cover_url == '/media/variants/1/960.webp'


def test_process_photos_are_never_the_cover(make_artwork):
    artwork = make_artwork()
    ArtworkImage.objects.create(
        artwork=artwork,
        original='originals/p.jpg',
        is_process=True,
        variants=[{'width': 480, 'height': 360, 'name': 'variants/p/480.webp'}],
    )

    assert (artwork.cover, artwork.cover_url, artwork.thumbnail_url) == (None, None, None)

    ArtworkImage.objects.create(
        artwork=artwork, original='originals/f.jpg', position=5, variants=[{'width': 480, 'height': 360, 'name': 'variants/f/480.webp'}]
    )

    assert artwork.cover_url == '/media/variants/f/480.webp'


def test_cover_url_without_images_is_none(make_artwork):
    assert make_artwork().cover_url is None


def test_admin_form_rejects_a_taken_home_page_spot(make_artwork):
    make_artwork(featured_order=1, is_published=True)

    form = ArtworkAdminForm(FORM_DATA | {'featured_order': '1', 'is_published': 'on'})

    assert form.errors['featured_order'] == ['Artwork with this Home page spot already exists.']


ADMIN_ADD = FORM_DATA | {
    'description': '',
    'images-TOTAL_FORMS': '1',
    'images-INITIAL_FORMS': '0',
    'images-MIN_NUM_FORMS': '0',
    'images-MAX_NUM_FORMS': '1000',
    'images-0-position': '0',
}


def test_admin_blocks_publishing_without_an_image(admin_client):
    response = admin_client.post('/admin/artworks/artwork/add/', ADMIN_ADD | {'is_published': 'on'})

    assert response.status_code == 200
    assert 'A published work needs at least one image' in response.content.decode()
    assert not Artwork.objects.exists()


def test_admin_blocks_publishing_with_only_a_process_photo(admin_client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    upload = SimpleUploadedFile('yard.png', _png(600, 400).getvalue(), content_type='image/png')

    response = admin_client.post(
        '/admin/artworks/artwork/add/',
        ADMIN_ADD | {'is_published': 'on', 'images-0-original': upload, 'images-0-is_process': 'on'},
    )

    assert response.status_code == 200
    assert 'at least one image of the finished work' in response.content.decode()


def test_admin_saves_an_unpublished_work_without_an_image(admin_client):
    response = admin_client.post('/admin/artworks/artwork/add/', ADMIN_ADD)

    assert response.status_code == 302
    assert Artwork.objects.get().title == 'A'


def test_admin_form_keeps_unpublished_works_off_the_home_page(db):
    form = ArtworkAdminForm(FORM_DATA | {'featured_order': '1'})

    assert form.errors['featured_order'] == ['Only published works can go on the home page.']


def test_admin_list_shows_status_badges(admin_client, make_artwork):
    make_artwork(title='Held', status=ArtworkStatus.AVAILABLE, price_pence=100, reserved_until=timezone.now() + timedelta(minutes=5))

    html = admin_client.get('/admin/artworks/artwork/').content.decode()

    assert 'Held' in html
    assert 'Reserved' in html
    assert 'bg-orange-100' in html
