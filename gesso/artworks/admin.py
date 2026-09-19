from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from gesso.artworks.models import Artwork, ArtworkImage


class ArtworkImageInline(TabularInline):
    model = ArtworkImage
    extra = 1


@admin.register(Artwork)
class ArtworkAdmin(ModelAdmin):
    list_display = (
        'title',
        'year',
        'is_published',
        'status',
    )
    list_filter = (
        'is_published',
        'status',
    )
    prepopulated_fields = {'slug': ('title',)}
    inlines = (ArtworkImageInline,)
