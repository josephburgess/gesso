import pytest

from .models import Artwork


@pytest.mark.django_db
def test_published_excludes_drafts():
    live = Artwork.objects.create(title="Live", slug="live", year=2024, is_published=True)
    Artwork.objects.create(title="Draft", slug="draft", year=2024)

    assert list(Artwork.objects.published()) == [live]
