from django.contrib import admin

from gesso.content.models import SiteContent


@admin.register(SiteContent)
class SiteContentAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteContent.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
