import csv
from urllib.parse import quote, urlencode

from django.contrib import admin
from django.db.models import F
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import action, display

from gesso.enquiries.models import Enquiry, Subscriber


@admin.register(Enquiry)
class EnquiryAdmin(ModelAdmin):
    list_display = ('thumbnail', 'name', 'topic', 'artwork', 'created_at', 'is_read')
    list_filter = ('topic',)
    list_display_links = ('thumbnail', 'name')
    search_fields = ('name', 'email', 'message')
    ordering = (F('read_at').asc(nulls_first=True), '-created_at')
    fields = ('name', 'email', 'reply', 'topic', 'artwork', 'message', 'created_at', 'read_at')
    readonly_fields = ('reply', 'created_at', 'read_at')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('artwork').prefetch_related('artwork__images')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @display(description='')
    def thumbnail(self, obj):
        if not obj.artwork or not obj.artwork.thumbnail_url:
            return ''
        return format_html('<img src="{}" alt="" style="height:48px;width:48px;object-fit:cover">', obj.artwork.thumbnail_url)

    @display(boolean=True, description='Read')
    def is_read(self, obj):
        return obj.read_at is not None

    @display(description='Reply')
    def reply(self, obj):
        about = obj.artwork.title if obj.artwork else 'your enquiry'
        quoted = '\n'.join(f'> {line}' for line in obj.message.splitlines())[:1500]
        query = urlencode({'subject': f'Re: {about}', 'body': f'\n\n{obj.name} wrote:\n{quoted}'}, quote_via=quote)
        return format_html('<a href="mailto:{}?{}" class="font-semibold text-primary-600 underline">Reply by email</a>', obj.email, query)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        Enquiry.objects.unread().filter(pk=object_id).update(read_at=timezone.now())
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(Subscriber)
class SubscriberAdmin(ModelAdmin):
    list_display = ('email', 'created_at')
    search_fields = ('email',)
    readonly_fields = ('email', 'created_at')
    actions_list = ('export_csv',)

    def has_add_permission(self, request):
        return False

    @action(description='Export CSV', url_path='export-csv', icon='download')
    def export_csv(self, request):
        response = HttpResponse(content_type='text/csv', headers={'Content-Disposition': 'attachment; filename="subscribers.csv"'})
        writer = csv.writer(response)
        writer.writerow(['email', 'signed_up'])
        for subscriber in Subscriber.objects.order_by('created_at'):
            writer.writerow([subscriber.email, subscriber.created_at.date().isoformat()])
        return response
