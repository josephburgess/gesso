from django.db import models
from django.db.models import F

from gesso.artworks.models import Artwork


def increment(model: type[models.Model], field: str, defaults: dict | None = None, **key) -> None:
    model.objects.get_or_create(**key, defaults=defaults or {})
    model.objects.filter(**key).update(**{field: F(field) + 1})


class DailyView(models.Model):
    day = models.DateField()
    path = models.CharField(max_length=255)
    artwork = models.ForeignKey(Artwork, null=True, blank=True, on_delete=models.SET_NULL, related_name='daily_views')
    views = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = (models.UniqueConstraint(fields=('day', 'path'), name='unique_daily_view'),)

    def __str__(self):
        return f'{self.path} on {self.day}'


class DailyReferrer(models.Model):
    day = models.DateField()
    host = models.CharField(max_length=255)
    visits = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = (models.UniqueConstraint(fields=('day', 'host'), name='unique_daily_referrer'),)

    def __str__(self):
        return f'{self.host} on {self.day}'


class DailyVisitors(models.Model):
    day = models.DateField(unique=True)
    visitors = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'daily visitors'

    def __str__(self):
        return f'{self.visitors} on {self.day}'
