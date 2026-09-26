from typing import Self

from django.db import models

from gesso.artworks.models import Artwork


class EnquiryQuerySet(models.QuerySet['Enquiry']):
    def unread(self) -> Self:
        return self.filter(read_at__isnull=True)


class Enquiry(models.Model):
    artwork = models.ForeignKey(Artwork, null=True, blank=True, on_delete=models.SET_NULL, related_name='enquiries')
    name = models.CharField(max_length=200)
    email = models.EmailField()
    message = models.TextField()
    read_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = EnquiryQuerySet.as_manager()

    class Meta:
        ordering = ('-created_at',)
        verbose_name_plural = 'enquiries'

    def __str__(self):
        return f'{self.name} <{self.email}>'
