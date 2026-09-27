from django.contrib import admin
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin
from unfold.decorators import action, display

from gesso.commerce.forms import ShipForm
from gesso.commerce.models import Order, OrderStatus
from gesso.commerce.services import send_shipped
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
        'courier',
        'tracking_link',
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

    @display(description='Tracking')
    def tracking_link(self, obj):
        if not obj.tracking_url:
            return ''
        return format_html('<a href="{}" target="_blank" rel="noopener">Track parcel</a>', obj.tracking_url)

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
        form = ShipForm(request.POST or None)
        if form.is_valid():
            order.mark_shipped(form.cleaned_data['courier'], form.cleaned_data['tracking_url'])
            if form.cleaned_data['notify'] and order.buyer_email:
                send_shipped(order)
            self.message_user(request, f'{order.artwork} marked shipped.')
            return redirect('admin:commerce_order_change', object_id)
        context = {
            **self.admin_site.each_context(request),
            'title': f'Ship {order.artwork}',
            'intro': f'To {order.buyer_name}. The buyer gets an email with the tracking link if you add one.',
            'form': form,
            'submit_label': 'Mark shipped',
            'back_url': reverse('admin:commerce_order_change', args=[object_id]),
        }
        return TemplateResponse(request, 'admin/action_form.html', context)
