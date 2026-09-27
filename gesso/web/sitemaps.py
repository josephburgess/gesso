from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from gesso.artworks.models import Artwork
from gesso.content.models import Page


class PageSitemap(Sitemap):
    def items(self):
        return ['home', 'work', 'about', 'contact']

    def location(self, obj):
        return reverse(obj)


class ArtworkSitemap(Sitemap):
    def items(self):
        return Artwork.objects.published()


class LegalPageSitemap(Sitemap):
    def items(self):
        return Page.objects.all()
