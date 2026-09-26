from typing import Self

from django.db import models

from gesso.artworks.models import Artwork


class Topic(models.TextChoices):
    GENERAL = 'general', 'General'
    BUYING = 'buying', 'Buying a work'
    COMMISSION = 'commission', 'Commission'
    PRESS = 'press', 'Exhibitions & press'


class EnquiryQuerySet(models.QuerySet['Enquiry']):
    def unread(self) -> Self:
        return self.filter(read_at__isnull=True)


class Enquiry(models.Model):
    artwork = models.ForeignKey(Artwork, null=True, blank=True, on_delete=models.SET_NULL, related_name='enquiries')
    name = models.CharField(max_length=200)
    email = models.EmailField()
    topic = models.CharField(max_length=20, choices=Topic, default=Topic.GENERAL, blank=True)
    message = models.TextField()
    read_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = EnquiryQuerySet.as_manager()

    class Meta:
        ordering = ('-created_at',)
        verbose_name_plural = 'enquiries'

    def __str__(self):
        return f'{self.name} <{self.email}>'


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.email
