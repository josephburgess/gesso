import json
import re
from datetime import timedelta

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.utils import timezone

from gesso.artworks.models import ArtworkImage, ArtworkStatus
from gesso.content.models import AboutImage, Page, SiteContent
from gesso.enquiries.models import Enquiry, Subscriber
from gesso.web.formatting import dimensions, paragraphs, price
from gesso.web.middleware import site_props
from gesso.web.views.work import responsive_image

INERTIA = {'X-Inertia': 'true'}


def test_published_artwork_renders(client, make_artwork):
    make_artwork(title='Live', slug='live', is_published=True)

    response = client.get('/work/live', headers=INERTIA)

    assert response.status_code == 200
    assert response.json()['component'] == 'Work/Show'
    assert response.json()['props']['artwork']['title'] == 'Live'


def test_artwork_page_offers_an_enquiry(client, make_artwork):
    make_artwork(slug='live', is_published=True)

    purchase = client.get('/work/live', headers=INERTIA).json()['props']['purchase']

    assert purchase == {
        'enquire_href': '/contact?artwork=live',
        'enquire_label': 'Enquire about this work',
        'action': None,
        'note': '',
        'notify': False,
    }


def test_reserved_artwork_keeps_its_price(client, make_artwork):
    make_artwork(
        slug='held',
        is_published=True,
        status=ArtworkStatus.AVAILABLE,
        price_pence=340000,
        reserved_until=timezone.now() + timedelta(minutes=5),
    )

    artwork = client.get('/work/held', headers=INERTIA).json()['props']['artwork']

    assert (artwork['status'], artwork['price']) == ('Reserved', '£3,400')


def test_available_artwork_can_be_purchased(client, make_artwork):
    content = SiteContent.load()
    content.delivery_pence = 8500
    content.save()
    make_artwork(slug='a', is_published=True, status=ArtworkStatus.AVAILABLE, price_pence=100)

    purchase = client.get('/work/a', headers=INERTIA).json()['props']['purchase']

    assert purchase['action'] == '/work/a/checkout'
    assert 'Plus £85 UK delivery.' in purchase['note']


def test_sold_artwork_offers_a_commission_and_a_heads_up(client, make_artwork):
    make_artwork(slug='gone', is_published=True, status=ArtworkStatus.SOLD)

    purchase = client.get('/work/gone', headers=INERTIA).json()['props']['purchase']

    assert purchase['action'] is None
    assert (purchase['enquire_href'], purchase['enquire_label']) == ('/contact?artwork=gone&topic=commission', 'Ask about a commission')
    assert purchase['notify'] is True


def test_contact_takes_the_topic_from_the_query(client, make_artwork):
    make_artwork(slug='gone', is_published=True, status=ArtworkStatus.SOLD)

    assert client.get('/contact?artwork=gone&topic=commission', headers=INERTIA).json()['props']['contact']['topic'] == 'commission'
    assert client.get('/contact?artwork=gone&topic=nonsense', headers=INERTIA).json()['props']['contact']['topic'] == 'buying'


def test_artwork_page_shows_every_processed_image_in_order(client, make_artwork):
    artwork = make_artwork(slug='multi', is_published=True)
    for name, position in (('second', 1), ('first', 0)):
        ArtworkImage.objects.create(
            artwork=artwork,
            original=f'originals/{name}.jpg',
            position=position,
            variants=[{'width': 480, 'height': 360, 'name': f'variants/{name}/480.webp'}],
        )
    ArtworkImage.objects.create(artwork=artwork, original='originals/processing.jpg', position=2)

    images = client.get('/work/multi', headers=INERTIA).json()['props']['artwork']['images']

    assert [image['src'] for image in images] == ['/media/variants/first/480.webp', '/media/variants/second/480.webp']


def test_artwork_framing_is_shown(client, make_artwork):
    make_artwork(slug='framed', is_published=True, framing='Framed in oak')

    artwork = client.get('/work/framed', headers=INERTIA).json()['props']['artwork']

    assert artwork['framing'] == 'Framed in oak'


def test_artwork_images_carry_their_alt_text(client, make_artwork):
    artwork = make_artwork(slug='live', is_published=True)
    ArtworkImage.objects.create(
        artwork=artwork,
        original='originals/a.png',
        alt='A grey harbour at dusk',
        variants=[{'width': 480, 'height': 320, 'name': 'variants/a/480.webp'}],
    )

    images = client.get('/work/live', headers=INERTIA).json()['props']['artwork']['images']

    assert [image['alt'] for image in images] == ['A grey harbour at dusk']


def test_draft_artwork_404s(client, make_artwork):
    make_artwork(slug='draft')

    response = client.get('/work/draft', headers=INERTIA)

    assert response.status_code == 404
    assert response.json()['component'] == 'NotFound'


def test_noindex_header_when_enabled(client, db, settings):
    settings.NOINDEX = True

    assert client.get('/about', headers=INERTIA).headers['X-Robots-Tag'] == 'noindex, nofollow'


def test_no_noindex_header_by_default(client, db):
    assert 'X-Robots-Tag' not in client.get('/about', headers=INERTIA).headers


def test_responsive_image():
    image = ArtworkImage(
        variants=[
            {'width': 480, 'height': 240, 'name': 'variants/1/480.webp'},
            {'width': 960, 'height': 480, 'name': 'variants/1/960.webp'},
        ]
    )

    assert responsive_image(image) == {
        'src': '/media/variants/1/960.webp',
        'srcset': '/media/variants/1/480.webp 480w, /media/variants/1/960.webp 960w',
        'width': 960,
        'height': 480,
        'thumb': '/media/variants/1/480.webp',
        'alt': '',
    }


@pytest.mark.parametrize(
    ('path', 'current'),
    [('/work', True), ('/work/some-painting', True), ('/workshop', False), ('/', False)],
)
def test_work_nav_current(rf, db, path, current):
    request = rf.get(path)
    request.user = AnonymousUser()

    assert site_props(request, SiteContent.load())['nav'][0]['current'] is current


@pytest.mark.parametrize(
    ('height', 'width', 'expected'),
    [(700, 500, '70 × 50 cm'), (705, 500, '70.5 × 50 cm')],
)
def test_dimensions(height, width, expected):
    assert dimensions(height, width) == expected


@pytest.mark.parametrize(('pence', 'expected'), [(340000, '£3,400'), (340050, '£3,400.50')])
def test_price(pence, expected):
    assert price(pence) == expected


def test_paragraphs():
    assert paragraphs('One.\r\n\r\nTwo\nlines.\n  \nThree.') == ['One.', 'Two\nlines.', 'Three.']


def test_about_renders(client, db):
    response = client.get('/about', headers=INERTIA)

    assert response.status_code == 200
    assert response.json()['component'] == 'About'


def test_contact_post_saves_enquiry(client, db):
    data = {'name': 'A', 'email': 'a@example.com', 'message': 'Hi'}

    response = client.post('/contact', data, content_type='application/json', headers=INERTIA)

    assert response.status_code == 302
    assert Enquiry.objects.get().name == 'A'


def test_contact_post_returns_errors(client, db):
    data = {'name': '', 'email': 'nope', 'message': ''}

    response = client.post('/contact', data, content_type='application/json', headers=INERTIA)

    assert response.status_code == 200
    assert response.json()['props']['errors'] == {
        'name': 'This field is required.',
        'email': 'Enter a valid email address.',
        'message': 'This field is required.',
    }
    assert not Enquiry.objects.exists()


def test_contact_spam_catcher_pretends_success(client, db):
    data = {'name': 'A', 'email': 'a@example.com', 'message': 'Hi', 'website': 'spam.example'}

    response = client.post('/contact', data, content_type='application/json', headers=INERTIA)

    assert response.status_code == 302
    assert not Enquiry.objects.exists()


def test_contact_rejects_non_json(client, db):
    assert client.post('/contact', {'name': 'A'}).status_code == 400


def test_home_features_published_works_in_order(client, make_artwork):
    make_artwork(title='Second', is_published=True, featured_order=2)
    make_artwork(title='First', is_published=True, featured_order=1)
    make_artwork(title='Draft')

    home = client.get('/', headers=INERTIA).json()['props']['home']

    assert [t['title'] for t in home['featured']] == ['First', 'Second']
    assert len(home['index']) == 2


def test_contact_prefills_artwork_from_query(client, make_artwork):
    make_artwork(title='Ferry Light', slug='ferry-light', is_published=True)

    contact = client.get('/contact?artwork=ferry-light', headers=INERTIA).json()['props']['contact']

    assert contact['artwork'] == {'title': 'Ferry Light', 'slug': 'ferry-light'}
    assert contact['topic'] == 'buying'


def test_contact_offers_topics_starting_on_general(client, db):
    contact = client.get('/contact', headers=INERTIA).json()['props']['contact']

    assert contact['topic'] == 'general'
    assert [t['label'] for t in contact['topics']] == ['General', 'Buying a work', 'Commission', 'Exhibitions & press']


def test_contact_links_enquiry_to_artwork(client, make_artwork):
    artwork = make_artwork(slug='ferry-light', is_published=True)
    data = {'name': 'A', 'email': 'a@example.com', 'message': 'Hi', 'artwork': 'ferry-light'}

    client.post('/contact', data, content_type='application/json', headers=INERTIA)

    assert Enquiry.objects.get().artwork == artwork


def test_checkout_sends_the_browser_to_stripe(client, make_artwork, stripe_sessions):
    make_artwork(slug='a', is_published=True, status=ArtworkStatus.AVAILABLE, price_pence=100)

    response = client.post('/work/a/checkout', headers=INERTIA)

    assert response.status_code == 409
    assert response.headers['X-Inertia-Location'] == 'https://checkout.stripe.test/pay'


def test_checkout_of_sold_work_goes_back_to_the_page(client, make_artwork, stripe_sessions):
    make_artwork(slug='a', is_published=True, status=ArtworkStatus.SOLD, price_pence=100)

    response = client.post('/work/a/checkout', headers=INERTIA)

    assert response.status_code == 302
    assert stripe_sessions == []


def test_contact_form_is_rate_limited(client, db):
    data = {'name': 'A', 'email': 'a@example.com', 'message': 'Hi'}

    for _ in range(6):
        response = client.post('/contact', data, content_type='application/json', headers=INERTIA)

    assert Enquiry.objects.count() == 5
    assert list(get_messages(response.wsgi_request))[-1].message == "You've sent a few messages already. Please try again in an hour."


def test_checkout_is_rate_limited(client, make_artwork, stripe_sessions):
    make_artwork(slug='a', is_published=True, status=ArtworkStatus.SOLD, price_pence=100)

    for _ in range(11):
        response = client.post('/work/a/checkout', headers=INERTIA)

    assert list(get_messages(response.wsgi_request))[-1].message == 'Too many checkout attempts. Please try again in an hour.'


def test_site_identity_comes_from_site_content(client, db):
    content = SiteContent.load()
    content.site_name = 'Studio Name'
    content.tagline = 'Painter'
    content.site_description = 'Paintings of the sea.'
    content.save()

    site = client.get('/about', headers=INERTIA).json()['props']['site']
    html = client.get('/about').content.decode()

    assert (site['name'], site['tagline']) == ('Studio Name', 'Painter')
    assert 'About · Studio Name</title>' in html
    assert '<meta name="description" content="Paintings of the sea.">' in html


def test_frontend_sentry_is_configured_from_settings(client, db, settings):
    settings.SENTRY_FRONTEND_DSN = 'https://public@example.ingest.sentry.io/1'

    html = client.get('/about').content.decode()

    assert '<meta name="sentry-dsn" content="https://public@example.ingest.sentry.io/1">' in html


def test_frontend_sentry_is_off_without_a_dsn(client, db):
    assert 'sentry-dsn' not in client.get('/about').content.decode()


def test_about_page_shows_processed_photos_in_order(client, db):
    content = SiteContent.load()
    for name, position in (('second', 1), ('first', 0)):
        AboutImage.objects.create(
            site_content=content,
            original=f'about/originals/{name}.png',
            alt=f'{name} photo',
            caption=f'{name} caption',
            position=position,
            variants=[{'width': 480, 'height': 320, 'name': f'about/variants/{name}/480.webp'}],
        )
    AboutImage.objects.create(site_content=content, original='about/originals/processing.png', alt='x', position=2)

    photos = client.get('/about', headers=INERTIA).json()['props']['about']['photos']

    assert [(p['image']['alt'], p['caption'], p['image']['src']) for p in photos] == [
        ('first photo', 'first caption', '/media/about/variants/first/480.webp'),
        ('second photo', 'second caption', '/media/about/variants/second/480.webp'),
    ]


def _structured_data(client, slug):
    html = client.get(f'/work/{slug}').content.decode()
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html)
    return json.loads(match.group(1)) if match else None


def test_sitemap_lists_pages_and_published_works(client, make_artwork):
    make_artwork(slug='live', is_published=True)
    make_artwork(slug='draft')

    xml = client.get('/sitemap.xml').content.decode()

    assert '/work/live</loc>' in xml
    assert '/about</loc>' in xml
    assert '/pages/privacy</loc>' in xml
    assert '/work/draft' not in xml


def test_robots_leaves_out_the_sitemap_until_launch(client, db, settings):
    settings.NOINDEX = True
    assert 'Sitemap:' not in client.get('/robots.txt').content.decode()

    settings.NOINDEX = False
    assert 'Sitemap: http://testserver/sitemap.xml' in client.get('/robots.txt').content.decode()


def test_available_work_has_structured_data_with_an_offer(client, make_artwork):
    make_artwork(slug='a', title='Ferry Light', is_published=True, status=ArtworkStatus.AVAILABLE, price_pence=340000)

    data = _structured_data(client, 'a')

    assert data['@type'] == 'VisualArtwork'
    assert data['name'] == 'Ferry Light'
    assert data['height'] == {'@type': 'QuantitativeValue', 'value': 70.0, 'unitCode': 'CMT'}
    assert (data['offers']['price'], data['offers']['availability']) == ('3400', 'https://schema.org/InStock')


def test_sold_and_not_for_sale_works_offers(client, make_artwork):
    make_artwork(slug='sold', is_published=True, status=ArtworkStatus.SOLD, price_pence=100)
    make_artwork(slug='nfs', is_published=True, status=ArtworkStatus.NOT_FOR_SALE)

    assert _structured_data(client, 'sold')['offers']['availability'] == 'https://schema.org/SoldOut'
    assert 'offers' not in _structured_data(client, 'nfs')


def test_structured_data_cannot_break_out_of_its_script_tag(client, make_artwork):
    make_artwork(slug='x', is_published=True, description='Nice </script><script>alert(1)</script>')

    html = client.get('/work/x').content.decode()

    assert '<script>alert(1)' not in html
    assert _structured_data(client, 'x')['description'] == 'Nice </script><script>alert(1)</script>'


def _image(artwork, name, position=0, **fields):
    return ArtworkImage.objects.create(
        artwork=artwork,
        original=f'originals/{name}.jpg',
        position=position,
        variants=[{'width': 480, 'height': 360, 'name': f'variants/{name}/480.webp'}],
        **fields,
    )


def test_appearance_is_shared_and_rendered_on_the_html_element(client, db):
    content = SiteContent.load()
    content.layout, content.work_layout, content.headings, content.motion = 'top', 'salon', 'sans', False
    content.show_index, content.about_layout, content.theme = False, 'above', 'gallery'
    content.save()

    site = client.get('/about', headers=INERTIA).json()['props']['site']
    html = client.get('/about').content.decode()

    assert site['appearance'] == {
        'theme': 'gallery',
        'layout': 'top',
        'work_layout': 'salon',
        'headings': 'sans',
        'italic_titles': False,
        'motion': False,
        'show_index': False,
        'about_layout': 'above',
    }
    assert '<html lang="en-GB" data-theme="gallery" data-mode="light" data-type="sans" data-titles="upright" data-motion="off">' in html


PREVIEW = (
    '/about?preview=1&theme=slate&layout=top&work_layout=stack&headings=garamond&titles=italic&motion=off&index=off&about_layout=above'
)


def test_staff_can_preview_appearance(admin_client):
    response = admin_client.get(PREVIEW, headers=INERTIA)

    assert response.json()['props']['site']['appearance'] == {
        'theme': 'slate',
        'layout': 'top',
        'work_layout': 'stack',
        'headings': 'garamond',
        'italic_titles': True,
        'motion': False,
        'show_index': False,
        'about_layout': 'above',
    }
    assert response.headers['X-Robots-Tag'] == 'noindex'
    assert response.headers['X-Frame-Options'] == 'SAMEORIGIN'
    assert 'no-store' in response.headers['Cache-Control']
    assert (
        'data-theme="slate" data-mode="light" data-type="garamond" data-titles="italic" data-motion="off"'
        in admin_client.get(PREVIEW).content.decode()
    )


def test_preview_ignores_unknown_values(admin_client):
    appearance = admin_client.get('/about?preview=1&theme=neon&layout=sideways&titles=slanted&motion=maybe', headers=INERTIA).json()[
        'props'
    ]['site']['appearance']

    assert (appearance['theme'], appearance['layout'], appearance['italic_titles'], appearance['motion']) == ('paper', 'rail', False, True)


def test_visitors_cannot_preview_appearance(client, db):
    response = client.get(PREVIEW, headers=INERTIA)

    assert response.json()['props']['site']['appearance']['layout'] == 'rail'
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert (
        'data-theme="paper" data-mode="light" data-type="serif" data-titles="upright" data-motion="on"'
        in client.get(PREVIEW).content.decode()
    )


def test_artwork_page_links_neighbours_and_wraps_around(client, make_artwork):
    make_artwork(title='Newest', slug='newest', year=2025, is_published=True)
    make_artwork(title='Middle', slug='middle', year=2024, is_published=True)
    make_artwork(title='Oldest', slug='oldest', year=2023, is_published=True)
    make_artwork(title='Draft', slug='draft', year=2022)

    first = client.get('/work/newest', headers=INERTIA).json()['props']
    last = client.get('/work/oldest', headers=INERTIA).json()['props']

    assert (first['prev']['title'], first['next']['title']) == ('Oldest', 'Middle')
    assert (last['prev']['title'], last['next']) == ('Middle', {'title': 'Newest', 'href': '/work/newest'})


def test_single_artwork_has_no_neighbours(client, make_artwork):
    make_artwork(slug='only', is_published=True)

    props = client.get('/work/only', headers=INERTIA).json()['props']

    assert (props['prev'], props['next']) == (None, None)


def test_process_photos_follow_the_finished_views(client, make_artwork):
    artwork = make_artwork(title='Harbour', slug='a', is_published=True, featured_order=1)
    _image(artwork, 'yard', position=0, is_process=True, caption='Drying in the yard', home_position=0)
    _image(artwork, 'front', position=1)

    images = client.get('/work/a', headers=INERTIA).json()['props']['artwork']['images']
    home = client.get('/', headers=INERTIA).json()['props']['home']

    assert [image['src'] for image in images] == ['/media/variants/front/480.webp', '/media/variants/yard/480.webp']
    assert home['featured'][0]['cover']['src'] == '/media/variants/front/480.webp'
    assert home['process'] == [
        {
            'image': {
                'src': '/media/variants/yard/480.webp',
                'srcset': '/media/variants/yard/480.webp 480w',
                'width': 480,
                'height': 360,
                'thumb': '/media/variants/yard/480.webp',
                'alt': '',
            },
            'caption': 'Drying in the yard',
            'title': 'Harbour',
        }
    ]


def test_home_shows_the_chosen_studio_photos_in_order(client, make_artwork):
    work = make_artwork(title='Work', is_published=True)
    draft = make_artwork(title='Draft')
    _image(work, 'unchosen', is_process=True)
    _image(work, 'second', is_process=True, home_position=1)
    _image(work, 'first', is_process=True, home_position=0)
    _image(draft, 'draft', is_process=True, home_position=2)

    process = client.get('/', headers=INERTIA).json()['props']['home']['process']

    assert [p['image']['src'] for p in process] == ['/media/variants/first/480.webp', '/media/variants/second/480.webp']


def test_pages_link_the_favicon(client, db):
    html = client.get('/about').content.decode()

    assert '<link rel="icon" href="/static/web/favicon.ico" sizes="48x48">' in html
    assert client.get('/favicon.ico')['Location'] == '/static/web/favicon.ico'


def test_social_links_are_shared_and_in_structured_data(client, make_artwork):
    content = SiteContent.load()
    content.social_links.create(label='Instagram', url='https://instagram.com/elise', position=0)
    make_artwork(slug='a', is_published=True)

    site = client.get('/about', headers=INERTIA).json()['props']['site']
    html = client.get('/work/a').content.decode()

    assert site['social'] == [{'label': 'Instagram', 'href': 'https://instagram.com/elise'}]
    assert '"sameAs": ["https://instagram.com/elise"]' in html


def _subscribe(client, **data):
    return client.post('/subscribe', {'email': 'Reader@Example.com'} | data, content_type='application/json')


def test_subscribe_adds_the_email_once(client, db):
    first = _subscribe(client)
    again = _subscribe(client, email='reader@example.com')

    assert first.json() == again.json() == {'message': "Thanks, you're on the list."}
    assert list(Subscriber.objects.values_list('email', flat=True)) == ['reader@example.com']


def test_subscribe_rejects_a_bad_email(client, db):
    response = _subscribe(client, email='nope')

    assert response.status_code == 400
    assert response.json()['errors'] == {'email': 'Enter a valid email address.'}
    assert not Subscriber.objects.exists()


def test_subscribe_spam_catcher_pretends_success(client, db):
    assert _subscribe(client, website='spam.example').status_code == 200
    assert not Subscriber.objects.exists()


def test_subscribe_is_rate_limited(client, db):
    for i in range(6):
        response = _subscribe(client, email=f'r{i}@example.com')

    assert response.status_code == 429
    assert Subscriber.objects.count() == 5


def test_legal_pages_are_ready_to_edit(db):
    assert list(Page.objects.values_list('slug', flat=True)) == ['terms', 'delivery-and-returns', 'privacy']


def test_page_splits_headings_from_paragraphs(client, db):
    Page.objects.create(title='Care', slug='care', body='Keep it dry.\n\n## Hanging\n\nUse two hooks.\nLevel them.')

    response = client.get('/pages/care', headers=INERTIA)

    assert response.json()['component'] == 'Page'
    assert response.json()['props']['page'] == {
        'title': 'Care',
        'blocks': [
            {'heading': False, 'text': 'Keep it dry.'},
            {'heading': True, 'text': 'Hanging'},
            {'heading': False, 'text': 'Use two hooks.\nLevel them.'},
        ],
    }


def test_unknown_page_404s(client, db):
    assert client.get('/pages/nothing-here').status_code == 404


def test_pages_are_shared_for_the_footer(client, db):
    site = client.get('/about', headers=INERTIA).json()['props']['site']

    assert [page['label'] for page in site['pages']] == ['Terms of sale', 'Delivery & returns', 'Privacy']
    assert site['privacy_href'] == '/pages/privacy'


def test_no_privacy_link_without_a_privacy_page(client, db):
    Page.objects.filter(slug=Page.PRIVACY).delete()

    assert client.get('/about', headers=INERTIA).json()['props']['site']['privacy_href'] is None


def test_work_link_preview_falls_back_to_the_details(client, make_artwork):
    artwork = make_artwork(title='Port of Dover', slug='dover', is_published=True, medium='Oil on board', year=2025)
    _image(artwork, 'dover')

    html = client.get('/work/dover?ref=share').content.decode()

    assert '<meta property="og:title" content="Port of Dover">' in html
    assert '<meta property="og:description" content="Oil on board, 70 × 50 cm, 2025.">' in html
    assert '<meta property="og:url" content="http://testserver/work/dover">' in html
    assert '<meta property="og:image" content="http://testserver/media/variants/dover/480.webp">' in html
    assert '<meta name="twitter:card" content="summary_large_image">' in html


def test_home_link_preview_uses_the_lead_work(client, make_artwork):
    _image(make_artwork(is_published=True, featured_order=1), 'lead')

    html = client.get('/').content.decode()

    assert '<meta property="og:image" content="http://testserver/media/variants/lead/480.webp">' in html


def test_pages_without_an_image_get_a_small_card(client, db):
    html = client.get('/contact').content.decode()

    assert '<meta name="twitter:card" content="summary">' in html
    assert 'og:image' not in html


def test_work_page_follows_the_chosen_order(client, make_artwork):
    make_artwork(title='Second', year=2026, position=1, is_published=True)
    make_artwork(title='First', year=2020, position=0, is_published=True)

    artworks = client.get('/work', headers=INERTIA).json()['props']['artworks']

    assert [a['title'] for a in artworks] == ['First', 'Second']
