import uuid
from datetime import datetime
from typing import Self

from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
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
    framing = models.CharField(max_length=200, blank=True, help_text='For example "Framed in oak" or "Unframed, ready to hang".')
    status = models.CharField(
        max_length=20,
        choices=ArtworkStatus,
        default=ArtworkStatus.NOT_FOR_SALE,
    )
    price_pence = models.PositiveIntegerField(null=True, blank=True)
    reserved_until = models.DateTimeField(null=True, blank=True, editable=False)
    description = models.TextField(blank=True)
    featured_order = models.PositiveSmallIntegerField(
        'home page spot',
        null=True,
        blank=True,
        unique=True,
        choices=((1, '1 (large hero)'), (2, '2')),
        help_text='Leave empty to keep this work off the home page.',
    )

    position = models.IntegerField(default=0)

    objects = ArtworkQuerySet.as_manager()

    class Meta:
        ordering = ('position', '-year', 'title')
        constraints = (
            models.CheckConstraint(
                condition=~models.Q(status=ArtworkStatus.AVAILABLE, price_pence__isnull=True),
                name='artwork_available_needs_price',
                violation_error_message='An available work needs a price.',
            ),
        )

    def __str__(self):
        return self.title

    def get_absolute_url(self) -> str:
        return reverse('work_show', args=[self.slug])

    def reserve(self, until: datetime) -> None:
        self.reserved_until = until
        self.save(update_fields=['reserved_until'])

    def release(self, until: datetime) -> None:
        Artwork.objects.filter(pk=self.pk, reserved_until=until).update(reserved_until=None)

    def relist(self) -> None:
        self.status = ArtworkStatus.AVAILABLE if self.price_pence is not None else ArtworkStatus.NOT_FOR_SALE
        self.save(update_fields=['status'])

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
    def cover(self) -> ArtworkImage | None:
        return next((image for image in self.images.all() if not image.is_process), None)

    @property
    def thumbnail_url(self) -> str | None:
        return self.cover.thumbnail_url if self.cover else None

    @property
    def cover_url(self) -> str | None:
        image = self.cover
        if image is None or not image.variants:
            return None
        return image.original.storage.url(image.variants[-1]['name'])

    @property
    def display_status(self) -> str:
        if self.status == ArtworkStatus.AVAILABLE and self.is_reserved:
            return 'Reserved'
        return ArtworkStatus(self.status).label


class ProcessedImage(models.Model):
    original = models.ImageField(upload_to='originals/')
    variants = models.JSONField(default=list, editable=False)
    alt = models.CharField('alt text', max_length=200, blank=True, help_text='Describe the image for people using screen readers.')

    variants_dir = 'variants'

    class Meta:
        abstract = True

    def __str__(self):
        return self.original.name

    def save(self, *args, **kwargs):
        new_upload = not self.original._committed  # ty: ignore[unresolved-attribute]
        super().save(*args, **kwargs)
        if new_upload:
            self.make_variants()

    @property
    def thumbnail_url(self) -> str | None:
        return self.original.storage.url(self.variants[0]['name']) if self.variants else None

    def replace(self, file) -> None:
        old = self.original.name
        self.original = file
        self.save()
        self.original.storage.delete(old)

    def delete_files(self) -> None:
        storage = self.original.storage
        for variant in self.variants:
            storage.delete(variant['name'])
        storage.delete(self.original.name)

    def make_variants(self):
        storage = self.original.storage

        for old in self.variants:
            storage.delete(old['name'])

        with self.original.open('rb') as f:
            rendered = processing.webp_variants(f)

        version = uuid.uuid4().hex[:8]
        self.variants = [
            {
                'width': v.width,
                'height': v.height,
                'name': storage.save(f'{self.variants_dir}/{self.pk}/{version}-{v.width}.webp', ContentFile(v.data)),
            }
            for v in rendered
        ]
        self.save(update_fields=['variants'])


class ArtworkImage(ProcessedImage):
    artwork = models.ForeignKey(Artwork, null=True, blank=True, on_delete=models.CASCADE, related_name='images')
    position = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    home_position = models.PositiveSmallIntegerField(null=True, blank=True, editable=False)
    caption = models.CharField(max_length=200, blank=True, help_text='Shown under process photos, e.g. "Drying in the yard".')
    is_process = models.BooleanField(
        'studio / process photo',
        default=False,
        help_text='Show in "In the studio" rather than as a view of the finished work.',
    )

    class Meta:
        ordering = ('is_process', 'position', 'pk')
