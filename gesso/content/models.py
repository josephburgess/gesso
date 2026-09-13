from django.db import models


class SiteContent(models.Model):
    statement = models.TextField(blank=True, help_text='Large statement on About page')
    biography = models.TextField(blank=True, help_text='About page content. Blank lines start new paragraphs.')

    class Meta:
        verbose_name = verbose_name_plural = 'site content'

    def __str__(self):
        return 'Site content'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> SiteContent:
        content, _ = cls.objects.get_or_create(pk=1)
        return content
