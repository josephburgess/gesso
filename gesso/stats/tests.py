import pytest

from gesso.stats.models import DailyReferrer, DailyView, DailyVisitors

INERTIA = {'X-Inertia': 'true'}


def _views() -> dict[str, int]:
    return dict(DailyView.objects.values_list('path', 'views'))


def test_counts_each_visitor_once_per_page_per_day(client, db):
    client.get('/about')
    client.get('/about', headers=INERTIA)
    client.get('/work')
    client.get('/about', REMOTE_ADDR='203.0.113.9')

    assert _views() == {'/about': 2, '/work': 1}
    assert DailyVisitors.objects.get().visitors == 2


def test_work_views_belong_to_the_artwork(client, make_artwork):
    artwork = make_artwork(slug='ferry-light', is_published=True)

    client.get('/work/ferry-light')

    assert DailyView.objects.get().artwork == artwork


@pytest.mark.parametrize(
    'headers',
    [
        {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1)'},
        {'X-Inertia': 'true', 'X-Inertia-Partial-Data': 'artworks', 'X-Inertia-Partial-Component': 'Home'},
        {'Sec-Purpose': 'prefetch'},
    ],
)
def test_ignores_bots_and_background_requests(client, db, headers):
    client.get('/about', headers=headers)

    assert _views() == {}
    assert not DailyVisitors.objects.exists()


def test_ignores_staff_admin_and_missing_pages(admin_client, client, db):
    admin_client.get('/about')
    admin_client.get('/admin/')
    client.get('/work/nothing-here')

    assert _views() == {}
    assert not DailyVisitors.objects.exists()


def test_records_where_visitors_came_from(client, db):
    client.get('/about', headers={'Referer': 'https://www.instagram.com/studio'})
    client.get('/work', headers={'Referer': 'http://testserver/about'})

    assert dict(DailyReferrer.objects.values_list('host', 'visits')) == {'instagram.com': 1}
