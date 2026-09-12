import io

import pytest
from PIL import Image

from gesso.artworks import processing
from gesso.artworks.models import Artwork


def _png(width, height):
    buffer = io.BytesIO()
    Image.new('RGB', (width, height)).save(buffer, 'PNG')
    buffer.seek(0)
    return buffer


def test_published_excludes_drafts(make_artwork):
    live = make_artwork(slug="live", is_published=True)
    make_artwork(slug="draft")

    assert list(Artwork.objects.published()) == [live]


def test_variants_never_upscale():
    variants = processing.webp_variants(_png(1000, 500))

    assert [(v.width, v.height) for v in variants] == [(480, 240), (960, 480), (1000, 500)]
