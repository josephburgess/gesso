import io
from gesso.artworks.admin import ArtworkAdminForm

from PIL import Image

from gesso.artworks import processing
from gesso.artworks.models import Artwork


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
    'title': 'A', 'slug': 'a', 'year': 2024, 'medium': 'Oil', 'status': 'available',
    'height_cm': '70.5', 'width_cm': '50', 'price': '3400.50',
}


def test_admin_form_converts_units(db):
    form = ArtworkAdminForm(FORM_DATA)
    assert form.is_valid(), form.errors

    artwork = form.save()

    assert (artwork.height_mm, artwork.width_mm, artwork.price_pence) == (705, 500, 340050)


def test_admin_form_needs_price_when_available(db):
    form = ArtworkAdminForm(FORM_DATA | {'price': ''})

    assert 'price' in form.errors
