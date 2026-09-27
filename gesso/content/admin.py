from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from gesso.artworks.forms import PositionedForm
from gesso.artworks.image_manager import ImageManager
from gesso.artworks.models import Artwork
from gesso.content.forms import AppearanceForm, SiteContentAdminForm
from gesso.content.models import AboutImage, CVEntry, Page, SiteContent, SocialLink

NOTES = {
    'rail': 'Name, menu and details in a column',
    'top': 'Slim bar, wider pages',
    'grid': 'Even rows',
    'salon': 'Staggered columns',
    'stack': 'One work at a time',
    'beside': 'Photo and statement side by side',
    'above': 'Large photo, words underneath',
}


class AboutImages(ImageManager):
    model = AboutImage
    fields = (('alt', 'Alt text'), ('caption', 'Caption'))
    name = 'content_aboutimage'
    prefix = 'about-images/'

    def owner(self, key):
        return {'site_content': SiteContent.load()}


class SocialLinkInline(TabularInline):
    model = SocialLink
    form = PositionedForm
    extra = 1
    fields = ('label', 'url', 'position')
    ordering_field = 'position'
    hide_ordering_field = True
    verbose_name_plural = 'Social links'


class CVEntryInline(TabularInline):
    model = CVEntry
    extra = 1
    fields = ('year', 'kind', 'title', 'venue', 'place', 'link')
    verbose_name_plural = 'Exhibitions and CV'


@admin.register(SiteContent)
class SiteContentAdmin(ModelAdmin):
    form = SiteContentAdminForm
    inlines = (CVEntryInline, SocialLinkInline)
    readonly_fields = ('about_photos',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        return redirect('admin:content_sitecontent_change', SiteContent.load().pk)

    @display(description='About page photos')
    def about_photos(self, obj):
        return AboutImages(self).render()

    def get_urls(self):
        return [
            path('appearance/', self.admin_site.admin_view(self.appearance_view), name='content_appearance'),
            *AboutImages(self).urls(),
            *super().get_urls(),
        ]

    def appearance_view(self, request):
        if not self.has_change_permission(request):
            raise PermissionDenied
        form = AppearanceForm(request.POST or None, instance=SiteContent.load())
        if form.is_valid():
            form.save()
            messages.success(request, 'Appearance saved. The live site now uses these settings.')
            return redirect('admin:content_appearance')
        artwork = Artwork.objects.published().first()
        pages = [('Home', reverse('home')), ('Work', reverse('work'))]
        if artwork:
            pages.append(('Artwork', artwork.get_absolute_url()))
        pages.append(('About', reverse('about')))
        context = {
            **self.admin_site.each_context(request),
            'title': 'Appearance',
            'form': form,
            'layouts': [(choice, NOTES[choice.data['value']]) for choice in form['layout'].subwidgets],
            'work_layouts': [(choice, NOTES[choice.data['value']]) for choice in form['work_layout'].subwidgets],
            'about_layouts': [(choice, NOTES[choice.data['value']]) for choice in form['about_layout'].subwidgets],
            'pages': pages,
        }
        return TemplateResponse(request, 'admin/content/appearance.html', context)


@admin.register(Page)
class PageAdmin(ModelAdmin):
    list_display = ('title', 'slug')
    fields = ('title', 'slug', 'body')
    prepopulated_fields = {'slug': ('title',)}
    ordering_field = 'position'
    hide_ordering_field = True
