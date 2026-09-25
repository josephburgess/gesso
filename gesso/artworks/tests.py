import io
from datetime import timedelta

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


def test_cover_url_without_images_is_none(make_artwork):
    assert make_artwork().cover_url is None
