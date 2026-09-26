from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from gesso.artworks.forms import ArtworkAdminForm, ArtworkImageFormSet
from gesso.artworks.models import Artwork, ArtworkImage


class ArtworkImageInline(TabularInline):
    model = ArtworkImage
    formset = ArtworkImageFormSet
    extra = 1
    fields = ('preview', 'original', 'position')
    readonly_fields = ('preview',)
    ordering_field = 'position'
    hide_ordering_field = True

    @display(description='Preview')
    def preview(self, obj):
        if not obj.thumbnail_url:
            return ''
        return format_html('<img src="{}" alt="" style="height:120px">', obj.thumbnail_url)


@admin.register(Artwork)
class ArtworkAdmin(ModelAdmin):
    form = ArtworkAdminForm
    list_display = ('thumbnail', 'title', 'year', 'status_label', 'is_published', 'featured_order')
    list_display_links = ('thumbnail', 'title')
    list_filter = ('is_published', 'status')
    search_fields = ('title', 'medium')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'year', 'medium', 'height_cm', 'width_cm', 'description')}),
        ('Sale', {'fields': ('status', 'price')}),
        ('On the site', {'fields': ('is_published', 'featured_order')}),
    )
    inlines = (ArtworkImageInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('images')

    def view_on_site(self, obj):
        return obj.get_absolute_url() if obj.is_published else None

    @display(description='')
    def thumbnail(self, obj):
        images = obj.images.all()
        url = images[0].thumbnail_url if images else None
        if not url:
            return ''
        return format_html('<img src="{}" alt="" style="height:48px;width:48px;object-fit:cover">', url)

    @display(description='Status', ordering='status', label={'Available': 'success', 'Reserved': 'warning', 'Sold': 'info'})
    def status_label(self, obj):
        return obj.display_status
