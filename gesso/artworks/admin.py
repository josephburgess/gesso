from django.contrib import admin

from .models import Artwork


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    list_display = ("title", "year", "is_published")
    list_filter = ("is_published",)
    prepopulated_fields = {"slug": ("title",)}
