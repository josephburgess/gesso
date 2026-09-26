from django.contrib.sitemaps.views import sitemap
from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView

from gesso.web.sitemaps import ArtworkSitemap, PageSitemap
from gesso.web.views import about, checkout, contact, home, seo, subscribe, work

urlpatterns = [
    path('robots.txt', seo.robots, name='robots'),
    path('favicon.ico', RedirectView.as_view(url=static('web/favicon.ico'), permanent=True)),
    path('sitemap.xml', sitemap, {'sitemaps': {'pages': PageSitemap, 'works': ArtworkSitemap}}, name='sitemap'),
    path('', home.page, name='home'),
    path('work', work.index, name='work'),
    path('work/<slug:slug>', work.show, name='work_show'),
    path('about', about.page, name='about'),
    path('contact', contact.page, name='contact'),
    path('subscribe', subscribe.subscribe, name='subscribe'),
    path('work/<slug:slug>/checkout', checkout.start, name='checkout'),
    path('checkout/success', checkout.success, name='checkout_success'),
    path('checkout/cancel/<uuid:order_id>', checkout.cancel, name='checkout_cancel'),
]
