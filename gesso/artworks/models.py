from datetime import datetime
from typing import Self

from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone

from gesso.artworks import processing


class ArtworkStatus(models.TextChoices):
    AVAILABLE = 'available', 'Available'
    SOLD = 'sold', 'Sold'
    NOT_FOR_SALE = 'not_for_sale', 'Not for sale'


class ArtworkQuerySet(models.QuerySet['Artwork']):
    def published(self) -> Self:
        return self.filter(is_published=True)


class Artwork(models.Model):
    images: models.Manager[ArtworkImage]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    year = models.PositiveSmallIntegerField()
    is_published = models.BooleanField(default=False)
    medium = models.CharField(max_length=200)
    width_mm = models.PositiveIntegerField()
    height_mm = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=ArtworkStatus,
        default=ArtworkStatus.NOT_FOR_SALE,
    )
    price_pence = models.PositiveIntegerField(null=True, blank=True)
    reserved_until = models.DateTimeField(null=True, blank=True, editable=False)
    description = models.TextField(blank=True)
    featured_order = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text='Show on the home page. Lower numbers come first.',
    )

    objects = ArtworkQuerySet.as_manager()

    class Meta:
        ordering = ('-year', 'title')
        constraints = (
            models.CheckConstraint(
                condition=~models.Q(status=ArtworkStatus.AVAILABLE, price_pence__isnull=True),
                name='artwork_available_needs_price',
                violation_error_message='An available work needs a price.',
            ),
        )

    def __str__(self):
        return self.title

    def reserve(self, until: datetime) -> None:
        self.reserved_until = until
        self.save(update_fields=['reserved_until'])

    def release(self, until: datetime) -> None:
        Artwork.objects.filter(pk=self.pk, reserved_until=until).update(reserved_until=None)

    def mark_sold(self) -> None:
        self.status = ArtworkStatus.SOLD
        self.reserved_until = None
        self.save(update_fields=['status', 'reserved_until'])

    @property
    def is_reserved(self) -> bool:
        return self.reserved_until is not None and self.reserved_until > timezone.now()

    @property
    def is_purchasable(self) -> bool:
        return self.status == ArtworkStatus.AVAILABLE and self.price_pence is not None and not self.is_reserved

    @property
    def display_status(self) -> str:
        if self.status == ArtworkStatus.AVAILABLE and self.is_reserved:
            return 'Reserved'
        return ArtworkStatus(self.status).label


class ArtworkImage(models.Model):
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name='images')
    original = models.ImageField(upload_to='originals/')
    position = models.PositiveSmallIntegerField(default=0)
    variants = models.JSONField(default=list, editable=False)

    class Meta:
        ordering = ('position', 'pk')

    def __str__(self):
        return self.original.name

    def save(self, *args, **kwargs):
        new_upload = not self.original._committed  # ty: ignore[unresolved-attribute]
        super().save(*args, **kwargs)
        if new_upload:
            self.make_variants()

    def make_variants(self):
        storage = self.original.storage

        for old in self.variants:
            storage.delete(old['name'])

        with self.original.open('rb') as f:
            rendered = processing.webp_variants(f)

        self.variants = [
            {
                'width': v.width,
                'height': v.height,
                'name': storage.save(f'variants/{self.pk}/{v.width}.webp', ContentFile(v.data)),
            }
            for v in rendered
        ]
        self.save(update_fields=['variants'])
