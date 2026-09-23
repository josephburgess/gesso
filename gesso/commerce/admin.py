from django.contrib import admin
from django.utils import timezone
from unfold.admin import ModelAdmin

from gesso.commerce.models import Order, OrderStatus
from gesso.web.formatting import price


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('artwork', 'status', 'buyer_name', 'total', 'created_at')
    list_filter = ('status',)
    fields = (
        'artwork', 'status', 'total', 'buyer_name', 'buyer_email', 'shipping_address',
        'created_at', 'expires_at', 'paid_at', 'shipped_at', 'stripe_session_id',
    )
    readonly_fields = fields
    actions = ('mark_shipped',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='Total')
    def total(self, obj):
        return price(obj.amount_pence + obj.delivery_pence)

    @admin.action(description='Mark shipped')
    def mark_shipped(self, request, queryset):
        count = queryset.filter(status=OrderStatus.PAID).update(status=OrderStatus.SHIPPED, shipped_at=timezone.now())
        self.message_user(request, f'{count} marked shipped.')
