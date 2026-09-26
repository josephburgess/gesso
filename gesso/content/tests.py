import io

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from gesso.content.forms import SiteContentAdminForm
from gesso.content.models import AboutImage, SiteContent


def test_load_is_a_singleton(db):
    first = SiteContent.load()
    first.statement = 'Hello'
    first.save()

    assert SiteContent.load().statement == 'Hello'
    assert SiteContent.objects.count() == 1


def test_admin_form_edits_delivery_in_pounds(db):
    content = SiteContent.load()
    content.delivery_pence = 8500
    content.save()

    form = SiteContentAdminForm({'site_name': 'Studio', 'delivery': '92.50'}, instance=content)

    assert form.initial['delivery'] == 85
    assert form.is_valid(), form.errors
    assert form.save().delivery_pence == 9250


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
