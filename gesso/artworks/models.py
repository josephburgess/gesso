from django.db import models


class Artwork(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    year = models.PositiveSmallIntegerField()
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.title
