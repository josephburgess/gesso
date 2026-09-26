from itertools import count

import pytest

from gesso.artworks.models import Artwork
from gesso.commerce import stripe_client

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


@pytest.fixture
def stripe_sessions(monkeypatch):
    created = []

    def create_checkout_session(order, success_url, cancel_url):
        created.append(order)
        return stripe_client.CheckoutSession(f'cs_test_{len(created)}', 'https://checkout.stripe.test/pay')

    monkeypatch.setattr(stripe_client, 'create_checkout_session', create_checkout_session)
    return created
