import pytest

from gesso.artworks.models import Artwork


@pytest.mark.django_db
def test_draft_artwork_404s(client):
    Artwork.objects.create(title="Draft", slug="draft", year=2024)

    assert client.get("/work/draft").status_code == 404
