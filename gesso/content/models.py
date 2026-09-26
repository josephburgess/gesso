from django.db import models

from gesso.artworks.models import ProcessedImage


class SiteContent(models.Model):
    about_images: models.Manager[AboutImage]

    site_name = models.CharField(max_length=100, default='Gesso', help_text='Shown in the header, browser tabs and the admin.')
    tagline = models.CharField(max_length=100, blank=True, help_text='Shown under the name in the header.')
    site_description = models.CharField(max_length=200, blank=True, help_text='Default text for search results and link previews.')
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


class AboutImage(ProcessedImage):
    site_content = models.ForeignKey(SiteContent, on_delete=models.CASCADE, related_name='about_images')
    original = models.ImageField(upload_to='about/originals/')
    alt = models.CharField('alt text', max_length=200, help_text='Describe the photo for people using screen readers.')
    caption = models.CharField(max_length=200, blank=True, help_text='Shown under the photo, for example a photo credit.')
    position = models.PositiveSmallIntegerField(default=0)

    variants_dir = 'about/variants'

    class Meta:
        ordering = ('position', 'pk')
