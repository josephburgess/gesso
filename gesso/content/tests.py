import io
import re

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from gesso.content.forms import SettingsForm
from gesso.content.models import AboutImage, SiteContent, SocialLink


def test_load_is_a_singleton(db):
    first = SiteContent.load()
    first.statement = 'Hello'
    first.save()

    assert SiteContent.load().statement == 'Hello'
    assert SiteContent.objects.count() == 1


def test_settings_form_edits_delivery_in_pounds(db):
    content = SiteContent.load()
    content.delivery_pence = 8500
    content.save()

    form = SettingsForm({'site_name': 'Studio', 'delivery': '92.50'}, instance=content)

    assert form.initial['delivery'] == 85
    assert form.is_valid(), form.errors
    assert form.save().delivery_pence == 9250


def test_settings_page_saves_email_and_social_links(admin_client):
    SocialLink.objects.create(site_content=SiteContent.load(), label='Instagram', url='https://instagram.com/studio')
    url = '/admin/content/sitesettings/1/change/'

    html = admin_client.get('/admin/content/sitesettings/', follow=True).content.decode()
    response = admin_client.post(
        url,
        {
            'site_name': 'Studio',
            'notification_email': 'studio@example.com',
            'delivery': '85',
            'social_links-TOTAL_FORMS': '0',
            'social_links-INITIAL_FORMS': '0',
        },
    )

    assert 'Instagram' in html
    assert response.status_code == 302
    assert SiteContent.load().notification_email == 'studio@example.com'


def test_site_text_is_only_copy(admin_client):
    html = admin_client.get('/admin/content/sitecontent/', follow=True).content.decode()

    assert 'name="biography"' in html
    assert not any(f'name="{field}"' in html for field in ('site_name', 'notification_email', 'delivery'))
    assert 'Social links' not in html


def _png(width=1200, height=800) -> SimpleUploadedFile:
    buffer = io.BytesIO()
    Image.new('RGB', (width, height), 'white').save(buffer, 'PNG')
    return SimpleUploadedFile('portrait.png', buffer.getvalue(), content_type='image/png')


def test_about_photos_get_their_own_variants(db, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    photo = AboutImage(site_content=SiteContent.load(), alt='In the studio', original=_png())
    photo.save()

    assert photo.original.name.startswith('about/originals/')
    assert photo.variants
    assert all(v['name'].startswith(f'about/variants/{photo.pk}/') for v in photo.variants)


def test_about_photos_need_alt_text(db):
    photo = AboutImage(site_content=SiteContent.load(), original='about/originals/a.png')

    with pytest.raises(ValidationError) as error:
        photo.full_clean()

    assert 'alt' in error.value.message_dict


def test_appearance_page_shows_the_current_choices(admin_client):
    content = SiteContent.load()
    content.work_layout = 'salon'
    content.save()

    html = admin_client.get('/admin/content/sitecontent/appearance/').content.decode()

    assert 'Staggered columns' in html
    assert re.search(r'value="salon"[^>]*checked', html)


def test_appearance_page_saves_the_settings(admin_client):
    response = admin_client.post(
        '/admin/content/sitecontent/appearance/',
        {'theme': 'slate', 'layout': 'top', 'work_layout': 'stack', 'headings': 'garamond', 'italic_titles': 'on', 'about_layout': 'above'},
        follow=True,
    )

    content = SiteContent.load()
    assert (
        content.theme,
        content.layout,
        content.work_layout,
        content.headings,
        content.italic_titles,
        content.motion,
        content.show_index,
        content.about_layout,
    ) == (
        'slate',
        'top',
        'stack',
        'garamond',
        True,
        False,
        False,
        'above',
    )
    assert 'Appearance saved. The live site now uses these settings.' in response.content.decode()


def test_appearance_page_needs_a_staff_login(client, db):
    response = client.get('/admin/content/sitecontent/appearance/')

    assert response.status_code == 302
    assert response['Location'].startswith('/admin/login/')


def test_about_photos_upload_and_take_alt_text(admin_client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    base = '/admin/content/sitecontent/about-images/'

    tile = admin_client.post(f'{base}upload/', {'file': _png()}).json()
    admin_client.post(f'{base}{tile["id"]}/', {'alt': 'In the studio', 'caption': ''})

    photo = SiteContent.load().about_images.get()
    assert (photo.alt, bool(photo.variants)) == ('In the studio', True)


def test_pages_admin_lists_the_legal_pages(admin_client):
    html = admin_client.get('/admin/content/page/').content.decode()

    assert 'Terms of sale' in html
    assert 'Privacy' in html
