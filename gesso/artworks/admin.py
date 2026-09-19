from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from gesso.artworks.forms import ArtworkAdminForm
from gesso.artworks.models import Artwork, ArtworkImage


class ArtworkImageInline(TabularInline):
    model = ArtworkImage
    extra = 1
    fields = ('preview', 'original', 'position')
    readonly_fields = ('preview',)

    @admin.display(description='Preview')
    def preview(self, obj):
        if not obj.variants:
            return ''
        return format_html('<img src="{}" style="height:80px">', obj.original.storage.url(obj.variants[0]['name']))


@admin.register(Artwork)
class ArtworkAdmin(ModelAdmin):
    form = ArtworkAdminForm
    list_display = (
        'title',
        'year',
        'is_published',
        'status',
        'featured_order'
    )
    list_filter = (
        'is_published',
        'status',
    )
    prepopulated_fields = {'slug': ('title',)}
    inlines = (ArtworkImageInline,)
