from django.db import models


class SiteContent(models.Model):
    intro = models.TextField(blank=True, help_text='Short text in the home page sidebar.')
    statement = models.TextField(blank=True, help_text='Large statement on About page')
    biography = models.TextField(blank=True, help_text='About page content. Blank lines start new paragraphs.')
    contact_details = models.TextField(blank=True, help_text='Contact page. Line breaks are kept.')
    notification_email = models.EmailField(blank=True, help_text='Where contact form enquiries are sent.')
    delivery_pence = models.PositiveIntegerField(default=0, help_text='Flat UK delivery charge added at checkout.')

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
