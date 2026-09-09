import pytest

from gesso.artworks.models import Artwork

INERTIA = {"X-Inertia": "true"}


@pytest.mark.django_db
def test_published_artwork_renders(client):
    Artwork.objects.create(title="Live", slug="live", year=2024, is_published=True)

    response = client.get("/work/live", headers=INERTIA)

    assert response.status_code == 200
    assert response.json()["component"] == "Work/Show"
    assert response.json()["props"]["artwork"] == {"title": "Live", "year": 2024}


@pytest.mark.django_db
def test_draft_artwork_404s(client):
    Artwork.objects.create(title="Draft", slug="draft", year=2024)

    assert client.get("/work/draft", headers=INERTIA).status_code == 404
