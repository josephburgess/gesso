import io
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import modelform_factory
from django.utils import timezone
from PIL import Image

from gesso.artworks import processing
from gesso.artworks.admin import ArtworkAdminForm
from gesso.artworks.forms import PositionedForm
from gesso.artworks.models import Artwork, ArtworkImage, ArtworkStatus
from gesso.content.models import SocialLink


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


ADMIN_ADD = FORM_DATA | {'description': ''}


def _upload(name='photo.png', size=(600, 400)):
    return SimpleUploadedFile(name, _png(*size).getvalue(), content_type='image/png')


def _pending(is_process=False):
    return ArtworkImage.objects.create(
        original='originals/p.jpg',
        is_process=is_process,
        variants=[{'width': 480, 'height': 360, 'name': 'variants/p/480.webp'}],
    )


def test_admin_blocks_publishing_without_an_image(admin_client):
    response = admin_client.post('/admin/artworks/artwork/add/', ADMIN_ADD | {'is_published': 'on'})

    assert response.status_code == 200
    assert 'A published work needs at least one image' in response.content.decode()
    assert not Artwork.objects.exists()


def test_admin_blocks_publishing_with_only_a_process_photo(admin_client):
    photo = _pending(is_process=True)

    response = admin_client.post('/admin/artworks/artwork/add/', ADMIN_ADD | {'is_published': 'on', 'image_ids': str(photo.pk)})

    assert response.status_code == 200
    assert 'at least one image of the finished work' in response.content.decode()


def test_admin_saves_an_unpublished_work_without_an_image(admin_client):
    response = admin_client.post('/admin/artworks/artwork/add/', ADMIN_ADD)

    assert response.status_code == 302
    assert Artwork.objects.get().title == 'A'


def test_admin_attaches_images_uploaded_before_the_first_save(admin_client):
    photo = _pending()

    response = admin_client.post('/admin/artworks/artwork/add/', ADMIN_ADD | {'is_published': 'on', 'image_ids': str(photo.pk)})

    assert response.status_code == 302
    photo.refresh_from_db()
    assert photo.artwork == Artwork.objects.get()


def test_admin_unpublishing_takes_a_work_off_the_home_page(admin_client, make_artwork):
    artwork = make_artwork(slug='a', is_published=True, featured_order=1)

    admin_client.post(f'/admin/artworks/artwork/{artwork.pk}/change/', ADMIN_ADD)

    artwork.refresh_from_db()
    assert artwork.featured_order is None


def test_image_manager_uploads_with_variants(admin_client, make_artwork, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    artwork = make_artwork()

    tile = admin_client.post(f'/admin/artworks/artwork/{artwork.pk}/images/upload/', {'file': _upload()}).json()

    image = artwork.images.get()
    assert tile == {'id': image.pk, 'thumb': image.thumbnail_url, 'alt': '', 'caption': '', 'is_process': False}
    assert image.variants


def test_image_manager_rejects_a_non_image(admin_client, make_artwork):
    artwork = make_artwork()
    upload = SimpleUploadedFile('notes.txt', b'hello', content_type='text/plain')

    response = admin_client.post(f'/admin/artworks/artwork/{artwork.pk}/images/upload/', {'file': upload})

    assert response.status_code == 400
    assert not artwork.images.exists()


def test_image_manager_replaces_in_place(admin_client, make_artwork, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    artwork = make_artwork()
    base = f'/admin/artworks/artwork/{artwork.pk}/images/'
    first = admin_client.post(f'{base}upload/', {'file': _upload('a.png')}).json()
    admin_client.post(f'{base}upload/', {'file': _upload('b.png')})
    admin_client.post(f'{base}{first["id"]}/', {'caption': 'Yard'})
    old = ArtworkImage.objects.get(pk=first['id'])
    old_files = [old.original.name, *(variant['name'] for variant in old.variants)]

    replaced = admin_client.post(f'{base}{first["id"]}/replace/', {'file': _upload('c.png', (500, 500))}).json()

    image = ArtworkImage.objects.get(pk=first['id'])
    assert (image.position, image.caption, image.variants[0]['height']) == (0, 'Yard', 480)
    assert replaced['thumb'] != first['thumb']
    assert not any((tmp_path / name).exists() for name in old_files)
    assert all((tmp_path / variant['name']).exists() for variant in image.variants)


def test_image_manager_updates_orders_and_deletes(admin_client, make_artwork, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    artwork = make_artwork()
    base = f'/admin/artworks/artwork/{artwork.pk}/images/'
    a, b = (admin_client.post(f'{base}upload/', {'file': _upload()}).json()['id'] for _ in range(2))

    admin_client.post(f'{base}{b}/', {'caption': 'Easel', 'is_process': 'on'})
    admin_client.post(f'{base}order/', f'{{"ids": [{b}, {a}]}}', content_type='application/json')
    admin_client.post(f'{base}{a}/delete/')

    [image] = artwork.images.all()
    assert (image.pk, image.caption, image.is_process, image.position) == (b, 'Easel', True, 0)


def test_image_manager_cleans_up_stale_pending_uploads(admin_client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    stale = _pending()
    ArtworkImage.objects.filter(pk=stale.pk).update(created_at=timezone.now() - timedelta(days=2))

    tile = admin_client.post('/admin/artworks/artwork/pending/images/upload/', {'file': _upload()}).json()

    assert list(ArtworkImage.objects.values_list('pk', flat=True)) == [tile['id']]


def test_image_manager_needs_staff(client, make_artwork):
    artwork = make_artwork()

    response = client.post(f'/admin/artworks/artwork/{artwork.pk}/images/upload/', {'file': _upload()})

    assert response.status_code == 302
    assert response['Location'].startswith('/admin/login/')


def _with_image(artwork, is_process=False):
    return ArtworkImage.objects.create(
        artwork=artwork,
        original='originals/x.jpg',
        is_process=is_process,
        variants=[{'width': 480, 'height': 360, 'name': 'variants/x/480.webp'}],
    )


def test_home_page_swaps_the_hero_without_a_clash(admin_client, make_artwork):
    old = make_artwork(is_published=True, featured_order=1)
    new = make_artwork(is_published=True)

    response = admin_client.post('/admin/artworks/artwork/home-page/', {'hero': new.pk, 'second': old.pk})

    assert response.status_code == 302
    old.refresh_from_db()
    new.refresh_from_db()
    assert (new.featured_order, old.featured_order) == (1, 2)


def test_home_page_rejects_the_same_work_twice(admin_client, make_artwork):
    work = make_artwork(is_published=True)

    response = admin_client.post('/admin/artworks/artwork/home-page/', {'hero': work.pk, 'second': work.pk})

    assert 'Choose a different work from the hero.' in response.content.decode()


def test_home_page_orders_up_to_two_studio_photos(admin_client, make_artwork):
    work = make_artwork(is_published=True)
    a, b, c = (_with_image(work, is_process=True) for _ in range(3))

    too_many = admin_client.post('/admin/artworks/artwork/home-page/', {'studio': [a.pk, b.pk, c.pk]})
    admin_client.post('/admin/artworks/artwork/home-page/', {'studio': [c.pk, a.pk]})

    assert 'Choose up to two studio photos.' in too_many.content.decode()
    positions = dict(ArtworkImage.objects.values_list('pk', 'home_position'))
    assert (positions[c.pk], positions[a.pk], positions[b.pk]) == (0, 1, None)


def test_positioned_form_ignores_a_blank_row_renumbered_by_reordering(db):
    form_class = modelform_factory(SocialLink, form=PositionedForm, fields=('label', 'url', 'position'))

    def form(**data):
        return form_class(data, empty_permitted=True, use_required_attribute=False)

    assert not form(label='', url='', position='3').has_changed()
    assert form(label='Instagram', url='', position='3').has_changed()


def test_admin_list_shows_status_badges(admin_client, make_artwork):
    make_artwork(title='Held', status=ArtworkStatus.AVAILABLE, price_pence=100, reserved_until=timezone.now() + timedelta(minutes=5))

    html = admin_client.get('/admin/artworks/artwork/').content.decode()

    assert 'Held' in html
    assert 'Reserved' in html
    assert 'bg-orange-100' in html


def test_admin_links_drafts_to_their_preview(admin_client, make_artwork):
    draft = make_artwork(slug='draft')

    html = admin_client.get(f'/admin/artworks/artwork/{draft.pk}/change/').content.decode()

    assert 'View on site' in html
