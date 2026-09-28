import json
from datetime import date, timedelta

from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.timezone import localtime

from gesso.artworks.models import Artwork
from gesso.commerce.models import Order, OrderStatus
from gesso.content.models import SiteContent
from gesso.enquiries.models import Enquiry, Subscriber
from gesso.stats.models import DailyReferrer, DailyView, DailyVisitors
from gesso.web.formatting import price

DAYS = 30


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


def _visitors_by_day(since: date, until: date) -> dict[date, int]:
    totals = dict(DailyVisitors.objects.filter(day__gte=since, day__lte=until).values_list('day', 'visitors'))
    return {since + timedelta(days=n): totals.get(since + timedelta(days=n), 0) for n in range((until - since).days + 1)}


def _change(current: int, previous: int) -> str:
    if not previous:
        return ''
    percent = round((current - previous) / previous * 100)
    return f'{percent:+}% on the {DAYS} days before'


def _counted(title: str, count: int) -> str:
    return f'{title} ({count})' if count else title


def _takings(year: int) -> int:
    sold = Order.objects.filter(paid_at__year=year, status__in=(OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.REFUNDED)).aggregate(
        total=Sum(F('amount_pence') + F('delivery_pence') - Coalesce('refund_pence', 0))
    )
    return sold['total'] or 0


def _most_viewed(since: date) -> list[tuple[Artwork, int]]:
    totals = (
        DailyView.objects.filter(day__gte=since, artwork__isnull=False)
        .values('artwork')
        .annotate(total=Sum('views'))
        .order_by('-total')[:8]
    )
    artworks = Artwork.objects.in_bulk([row['artwork'] for row in totals])
    return [(artworks[row['artwork']], row['total']) for row in totals]


def dashboard_callback(request: HttpRequest, context: dict) -> dict:
    to_ship = Order.objects.to_ship().select_related('artwork').order_by('paid_at')
    unread = Enquiry.objects.unread().select_related('artwork')
    featured = {a.featured_order: a for a in Artwork.objects.exclude(featured_order=None).prefetch_related('images')}

    today = timezone.localdate()
    since = today - timedelta(days=DAYS - 1)
    before = since - timedelta(days=DAYS)
    visitors = _visitors_by_day(since, today)
    previous_visitors = DailyVisitors.objects.filter(day__gte=before, day__lt=since).aggregate(total=Sum('visitors'))['total'] or 0
    enquiries = Enquiry.objects.filter(created_at__date__gte=since).count()
    previous_enquiries = Enquiry.objects.filter(created_at__date__gte=before, created_at__date__lt=since).count()

    context['stats'] = [
        {
            'label': f'Visitors, last {DAYS} days',
            'value': f'{sum(visitors.values()):,}',
            'note': _change(sum(visitors.values()), previous_visitors),
        },
        {
            'label': f'Sales in {today.year}',
            'value': price(_takings(today.year)),
            'note': 'Including delivery, less refunds',
            'href': reverse('admin:commerce_order_changelist'),
        },
        {
            'label': f'Enquiries, last {DAYS} days',
            'value': enquiries,
            'note': _change(enquiries, previous_enquiries),
            'href': reverse('admin:enquiries_enquiry_changelist'),
        },
        {
            'label': f'New subscribers, last {DAYS} days',
            'value': Subscriber.objects.filter(created_at__date__gte=since).count(),
            'note': f'{Subscriber.objects.count():,} on the list',
            'href': reverse('admin:enquiries_subscriber_changelist'),
        },
    ]
    context['visitors_chart'] = json.dumps(
        {
            'labels': [date_format(day, 'j M') for day in visitors],
            'datasets': [
                {
                    'label': 'Visitors',
                    'data': list(visitors.values()),
                    'borderColor': 'var(--color-primary-600)',
                    'backgroundColor': 'var(--color-primary-600)',
                    'pointRadius': 0,
                    'tension': 0.3,
                    'displayYAxis': True,
                }
            ],
        }
    )
    context['works_table'] = {
        'headers': ['Work', 'Visitors'],
        'rows': [[_artwork_link(artwork), f'{total:,}'] for artwork, total in _most_viewed(since)],
    }
    context['referrers_table'] = {
        'headers': ['Site', 'Visits'],
        'rows': [
            [row['host'], f'{row["total"]:,}']
            for row in DailyReferrer.objects.filter(day__gte=since)
            .values('host')
            .annotate(total=Sum('visits'))
            .order_by('-total', 'host')[:8]
        ],
    }
    context['orders_title'] = _counted('Orders to ship', to_ship.count())
    context['enquiries_title'] = _counted('Unread enquiries', unread.count())
    context['orders_table'] = {
        'headers': ['Work', 'Buyer', 'Total', 'Paid'],
        'rows': [
            [
                _link(reverse('admin:commerce_order_change', args=[order.pk]), order.artwork.title),
                order.buyer_name,
                price(order.total_pence),
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
    context['home_page'] = [
        {
            'label': label,
            'artwork': featured.get(spot),
            'href': reverse('admin:artworks_artwork_change', args=[featured[spot].pk]) if spot in featured else None,
        }
        for spot, label in ((1, 'Hero'), (2, 'Second'))
    ]
    context['without_images'] = [_artwork_link(a) for a in Artwork.objects.filter(images__isnull=True)]
    context['without_alt'] = [_artwork_link(a) for a in Artwork.objects.filter(images__alt='').distinct()]
    context['actions'] = [
        {'label': 'Add a work', 'href': reverse('admin:artworks_artwork_add')},
        {'label': 'Edit site text', 'href': reverse('admin:content_sitecontent_changelist')},
        {'label': 'Change appearance', 'href': reverse('admin:content_appearance')},
        {'label': 'Settings', 'href': reverse('admin:content_sitesettings_changelist')},
        {'label': 'View site', 'href': '/'},
    ]
    return context
