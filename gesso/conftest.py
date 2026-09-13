from itertools import count

import pytest

from gesso.artworks.models import Artwork

_n = count(1)


@pytest.fixture
def make_artwork(db):
    def make(**fields):
        n = next(_n)
        defaults = {
            'title': f'Artwork {n}',
            'slug': f'artwork-{n}',
            'year': 2024,
            'medium': 'Oil on canvas',
            'width_mm': 500,
            'height_mm': 700,
        }
        return Artwork.objects.create(**(defaults | fields))

    return make
