from django.contrib import admin
from django.utils import timezone
from unfold.admin import ModelAdmin

from gesso.enquiries.models import Enquiry


@admin.register(Enquiry)
class EnquiryAdmin(ModelAdmin):
    list_display = ('name', 'email', 'artwork', 'created_at', 'is_read')
    search_fields = ('name', 'email', 'message')
    fields = ('name', 'email', 'artwork', 'message', 'created_at', 'read_at')
    readonly_fields = ('created_at', 'read_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(boolean=True, description='Read')
    def is_read(self, obj):
        return obj.read_at is not None

    def change_view(self, request, object_id, form_url='', extra_context=None):
        Enquiry.objects.unread().filter(pk=object_id).update(read_at=timezone.now())
        return super().change_view(request, object_id, form_url, extra_context)
