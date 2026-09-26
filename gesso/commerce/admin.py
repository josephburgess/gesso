from django.contrib import admin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin
from unfold.decorators import action, display

from gesso.commerce.models import Order, OrderStatus
from gesso.web.formatting import price


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('artwork', 'status_label', 'buyer_name', 'total', 'paid_at')
    list_filter = ('status',)
    fields = (
        'artwork',
        'status',
        'total',
        'buyer_name',
        'buyer_email',
        'address_label',
        'created_at',
        'paid_at',
        'shipped_at',
        'stripe_link',
    )
    readonly_fields = fields
    actions = ('mark_shipped',)
    actions_detail = ('ship',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_ship_permission(self, request, object_id=None):
        return object_id is not None and Order.objects.to_ship().filter(pk=object_id).exists()

    @display(description='Total')
    def total(self, obj):
        return price(obj.amount_pence + obj.delivery_pence)

    @display(description='Status', ordering='status', label={'Paid': 'warning', 'Shipped': 'success', 'Pending': 'info'})
    def status_label(self, obj):
        return OrderStatus(obj.status).label

    @display(description='Address label')
    def address_label(self, obj):
        return format_html_join(mark_safe('<br>'), '{}', ((line,) for line in obj.shipping_address.splitlines()))

    @display(description='Stripe')
    def stripe_link(self, obj):
        if not obj.stripe_session_id:
            return ''
        return format_html(
            '<a href="https://dashboard.stripe.com/search?query={}" target="_blank" rel="noopener">Find payment in Stripe</a>',
            obj.stripe_session_id,
        )

    @admin.action(description='Mark shipped')
    def mark_shipped(self, request, queryset):
        count = queryset.to_ship().update(status=OrderStatus.SHIPPED, shipped_at=timezone.now())
        self.message_user(request, f'{count} marked shipped.')

    @action(description='Mark shipped', url_path='ship', icon='local_shipping', permissions=['ship'])
    def ship(self, request, object_id):
        order = get_object_or_404(Order, pk=object_id)
        order.mark_shipped()
        self.message_user(request, f'{order.artwork} marked shipped.')
        return redirect('admin:commerce_order_change', object_id)
