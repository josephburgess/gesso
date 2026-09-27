from django.http import HttpRequest
from django.urls import reverse
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.timezone import localtime

from gesso.artworks.models import Artwork, ArtworkStatus
from gesso.commerce.models import Order
from gesso.content.models import SiteContent
from gesso.enquiries.models import Enquiry
from gesso.web.formatting import price


def site_name(request: HttpRequest) -> str:
    return SiteContent.load().site_name


def works_active(request: HttpRequest) -> bool:
    return request.path.startswith(reverse('admin:artworks_artwork_changelist')) and request.path != reverse('admin:artworks_homepage')


def site_text_active(request: HttpRequest) -> bool:
    return request.path.startswith(reverse('admin:content_sitecontent_changelist')) and request.path != reverse('admin:content_appearance')


def orders_to_ship(request: HttpRequest) -> int | None:
    return Order.objects.to_ship().count() or None


def unread_enquiries(request: HttpRequest) -> int | None:
    return Enquiry.objects.unread().count() or None


def _link(url: str, text: str) -> str:
    return format_html('<a href="{}" class="text-primary-600 underline">{}</a>', url, text)


def _artwork_link(artwork: Artwork) -> str:
    return _link(reverse('admin:artworks_artwork_change', args=[artwork.pk]), artwork.title)


def dashboard_callback(request: HttpRequest, context: dict) -> dict:
    to_ship = Order.objects.to_ship().select_related('artwork').order_by('paid_at')
    unread = Enquiry.objects.unread().select_related('artwork')
    featured = {a.featured_order: a for a in Artwork.objects.exclude(featured_order=None)}

    context['stats'] = [
        {
            'label': 'Orders to ship',
            'value': to_ship.count(),
            'href': reverse('admin:commerce_order_changelist') + '?status__exact=paid',
        },
        {'label': 'Unread enquiries', 'value': unread.count(), 'href': reverse('admin:enquiries_enquiry_changelist')},
        {
            'label': 'Works for sale',
            'value': Artwork.objects.published().filter(status=ArtworkStatus.AVAILABLE).count(),
            'href': reverse('admin:artworks_artwork_changelist') + '?status__exact=available',
        },
        {
            'label': 'Published works',
            'value': Artwork.objects.published().count(),
            'href': reverse('admin:artworks_artwork_changelist') + '?is_published__exact=1',
        },
    ]
    context['orders_table'] = {
        'headers': ['Work', 'Buyer', 'Total', 'Paid'],
        'rows': [
            [
                _link(reverse('admin:commerce_order_change', args=[order.pk]), order.artwork.title),
                order.buyer_name,
                price(order.amount_pence + order.delivery_pence),
                date_format(localtime(order.paid_at), 'j M') if order.paid_at else '',
            ]
            for order in to_ship
        ],
    }
    context['enquiries_table'] = {
        'headers': ['From', 'About', 'Received'],
        'rows': [
            [
                _link(reverse('admin:enquiries_enquiry_change', args=[enquiry.pk]), enquiry.name),
                enquiry.artwork.title if enquiry.artwork else '',
                date_format(localtime(enquiry.created_at), 'j M'),
            ]
            for enquiry in unread[:8]
        ],
    }
    context['home_page_table'] = {
        'headers': ['Spot', 'Work'],
        'rows': [
            [label, _artwork_link(featured[spot]) if spot in featured else 'Empty'] for spot, label in ((1, '1 (large hero)'), (2, '2'))
        ],
    }
    context['without_images'] = [_artwork_link(a) for a in Artwork.objects.filter(images__isnull=True)]
    context['without_alt'] = [_artwork_link(a) for a in Artwork.objects.filter(images__alt='').distinct()]
    context['actions'] = [
        {'label': 'Add a work', 'href': reverse('admin:artworks_artwork_add')},
        {'label': 'Edit site text', 'href': reverse('admin:content_sitecontent_changelist')},
        {'label': 'Change appearance', 'href': reverse('admin:content_appearance')},
        {'label': 'View site', 'href': '/'},
    ]
    return context
