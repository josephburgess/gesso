from django.db import models
from django.urls import reverse

from gesso.artworks.models import ProcessedImage


class SiteLayout(models.TextChoices):
    RAIL = 'rail', 'Side rail'
    TOP = 'top', 'Top bar'


class WorkLayout(models.TextChoices):
    GRID = 'grid', 'Grid'
    SALON = 'salon', 'Salon'
    STACK = 'stack', 'Exhibition'


class AboutLayout(models.TextChoices):
    BESIDE = 'beside', 'Portrait beside statement'
    ABOVE = 'above', 'Portrait above'


class Theme(models.TextChoices):
    PAPER = 'paper', 'Paper'
    GALLERY = 'gallery', 'Gallery'
    SLATE = 'slate', 'Slate'


class Headings(models.TextChoices):
    SERIF = 'serif', 'Caslon'
    GARAMOND = 'garamond', 'Garamond'
    SANS = 'sans', 'Modern sans'


class SiteContent(models.Model):
    about_images: models.Manager[AboutImage]
    social_links: models.Manager[SocialLink]

    site_name = models.CharField(max_length=100, default='Gesso', help_text='Shown in the header, browser tabs and the admin.')
    tagline = models.CharField(max_length=100, blank=True, help_text='Shown under the name in the header.')
    site_description = models.CharField(max_length=200, blank=True, help_text='Default text for search results and link previews.')
    intro = models.TextField(blank=True, help_text='Short text in the home page sidebar.')
    statement = models.TextField(blank=True, help_text='Large statement on About page')
    biography = models.TextField(blank=True, help_text='About page content. Blank lines start new paragraphs.')
    contact_details = models.TextField(blank=True, help_text='Contact page. Line breaks are kept.')
    notification_email = models.EmailField(blank=True, help_text='Where contact form enquiries are sent.')
    delivery_pence = models.PositiveIntegerField(default=0, help_text='Flat UK delivery charge added at checkout.')
    layout = models.CharField(max_length=20, choices=SiteLayout, default=SiteLayout.RAIL, help_text='Where the name and menu sit.')
    work_layout = models.CharField(
        max_length=20, choices=WorkLayout, default=WorkLayout.GRID, help_text='How the full list of works is arranged.'
    )
    theme = models.CharField(
        max_length=20,
        choices=Theme,
        default=Theme.PAPER,
        help_text='Colours for the whole site. Visitors can switch between its light and dark versions. Artwork is never tinted.',
    )
    headings = models.CharField(max_length=20, choices=Headings, default=Headings.SERIF)
    show_index = models.BooleanField(
        'index of works on the home page', default=True, help_text='A list of every work under the featured ones.'
    )
    about_layout = models.CharField(
        max_length=20, choices=AboutLayout, default=AboutLayout.BESIDE, help_text='How the About page is arranged.'
    )
    italic_titles = models.BooleanField('italic artwork titles', default=False, help_text='Set work titles in italic, as in a catalogue.')
    motion = models.BooleanField(
        'gentle motion',
        default=True,
        help_text='Images fade in, pages ease in and pictures zoom a little on hover. Always off for visitors who ask for reduced motion.',
    )

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


class SiteSettings(SiteContent):
    class Meta:
        proxy = True
        verbose_name = verbose_name_plural = 'settings'

    def __str__(self):
        return 'Settings'


class AboutImage(ProcessedImage):
    site_content = models.ForeignKey(SiteContent, on_delete=models.CASCADE, related_name='about_images')
    original = models.ImageField(upload_to='about/originals/')
    alt = models.CharField('alt text', max_length=200, help_text='Describe the photo for people using screen readers.')
    caption = models.CharField(max_length=200, blank=True, help_text='Shown under the photo, for example a photo credit.')
    position = models.PositiveSmallIntegerField(default=0)

    variants_dir = 'about/variants'

    class Meta:
        ordering = ('position', 'pk')


class SocialLink(models.Model):
    site_content = models.ForeignKey(SiteContent, on_delete=models.CASCADE, related_name='social_links')
    label = models.CharField(max_length=50, help_text='For example Instagram.')
    url = models.URLField('link')
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ('position', 'pk')

    def __str__(self):
        return self.label


class Page(models.Model):
    TERMS = 'terms'
    RETURNS = 'delivery-and-returns'
    PRIVACY = 'privacy'

    title = models.CharField(max_length=100)
    slug = models.SlugField(
        unique=True, help_text='The end of the web address. Checkout links to "terms" and the mailing list to "privacy".'
    )
    body = models.TextField(help_text='Blank lines start new paragraphs. Start a paragraph with ## to make it a heading.')
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ('position', 'pk')

    def __str__(self):
        return self.title

    def get_absolute_url(self) -> str:
        return reverse('page', args=[self.slug])
