from django.contrib import admin
from django.shortcuts import redirect
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display

from gesso.content.forms import SiteContentAdminForm
from gesso.content.models import AboutImage, SiteContent


class AboutImageInline(TabularInline):
    model = AboutImage
    extra = 1
    fields = ('preview', 'original', 'alt', 'caption', 'position')
    readonly_fields = ('preview',)
    ordering_field = 'position'
    hide_ordering_field = True
    verbose_name_plural = 'About page photos'

    @display(description='Preview')
    def preview(self, obj):
        if not obj.thumbnail_url:
            return ''
        return format_html('<img src="{}" alt="" style="height:120px">', obj.thumbnail_url)


@admin.register(SiteContent)
class SiteContentAdmin(ModelAdmin):
    form = SiteContentAdminForm
    inlines = (AboutImageInline,)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        return redirect('admin:content_sitecontent_change', SiteContent.load().pk)
