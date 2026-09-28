from django.db import models
from django.db.models import F

from gesso.artworks.models import Artwork


class DailyView(models.Model):
    day = models.DateField()
    path = models.CharField(max_length=255)
    artwork = models.ForeignKey(Artwork, null=True, blank=True, on_delete=models.SET_NULL, related_name='daily_views')
    views = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = (models.UniqueConstraint(fields=('day', 'path'), name='unique_daily_view'),)

    def __str__(self):
        return f'{self.path} on {self.day}'

    @classmethod
    def record(cls, day, path: str, artwork: Artwork | None = None) -> None:
        if not cls.objects.filter(day=day, path=path).update(views=F('views') + 1):
            cls.objects.get_or_create(day=day, path=path, defaults={'artwork': artwork})
            cls.objects.filter(day=day, path=path).update(views=F('views') + 1)


class DailyReferrer(models.Model):
    day = models.DateField()
    host = models.CharField(max_length=255)
    visits = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = (models.UniqueConstraint(fields=('day', 'host'), name='unique_daily_referrer'),)

    def __str__(self):
        return f'{self.host} on {self.day}'

    @classmethod
    def record(cls, day, host: str) -> None:
        if not cls.objects.filter(day=day, host=host).update(visits=F('visits') + 1):
            cls.objects.get_or_create(day=day, host=host)
            cls.objects.filter(day=day, host=host).update(visits=F('visits') + 1)
