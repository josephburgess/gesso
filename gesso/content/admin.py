from django.contrib import admin
from django.shortcuts import redirect
from unfold.admin import ModelAdmin

from gesso.content.models import SiteContent


@admin.register(SiteContent)
class SiteContentAdmin(ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        return redirect('admin:content_sitecontent_change', SiteContent.load().pk)
