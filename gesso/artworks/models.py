from django.db import models


class ArtworkQuerySet(models.QuerySet["Artwork"]):
    def published(self):
        return self.filter(is_published=True)

class Artwork(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    year = models.PositiveSmallIntegerField()
    is_published = models.BooleanField(default=False)

    objects = ArtworkQuerySet.as_manager()

    class Meta:
        ordering = ('-year', 'title')

    def __str__(self):
        return self.title
