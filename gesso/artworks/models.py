from typing import Self

from django.core.files.base import ContentFile
from django.db import models

from gesso.artworks import processing
from gesso.artworks.constants import ArtworkConstants


class ArtworkQuerySet(models.QuerySet['Artwork']):
    def published(self) -> Self:
        return self.filter(is_published=True)


class Artwork(ArtworkConstants, models.Model):
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
        choices=ArtworkConstants.STATUS_CHOICES,
        default=ArtworkConstants.STATUS_NOT_FOR_SALE,
    )
    price_pence = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)

    objects = ArtworkQuerySet.as_manager()

    class Meta:
        ordering = ('-year', 'title')
        constraints = (
            models.CheckConstraint(
                condition=~models.Q(status=ArtworkConstants.STATUS_AVAILABLE, price_pence__isnull=True),
                name='artwork_available_needs_price',
                violation_error_message='An available work needs a price.',
            ),
        )


    def __str__(self):
        return self.title


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
        with self.original.open('rb') as f:
            rendered = processing.webp_variants(f)
        storage = self.original.storage
        self.variants = [
            {
                'width': v.width,
                'height': v.height,
                'name': storage.save(f'variants/{self.pk}/{v.width}.webp', ContentFile(v.data)),
            }
            for v in rendered
        ]
        self.save(update_fields=['variants'])
