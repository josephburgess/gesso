import uuid
from typing import Self

from django.db import models
from django.utils import timezone

from gesso.artworks.models import Artwork


class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PAID = 'paid', 'Paid'
    SHIPPED = 'shipped', 'Shipped'
    EXPIRED = 'expired', 'Expired'
    REFUNDED = 'refunded', 'Refunded'


class OrderSource(models.TextChoices):
    ONLINE = 'online', 'Online'
    EXHIBITION = 'exhibition', 'Exhibition'
    PRIVATE = 'private', 'Private sale'


class OrderQuerySet(models.QuerySet['Order']):
    def to_ship(self) -> Self:
        return self.filter(status=OrderStatus.PAID)


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artwork = models.ForeignKey(Artwork, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=20, choices=OrderStatus, default=OrderStatus.PENDING)
    source = models.CharField(max_length=20, choices=OrderSource, default=OrderSource.ONLINE)
    venue = models.CharField(max_length=200, blank=True)
    amount_pence = models.PositiveIntegerField()
    delivery_pence = models.PositiveIntegerField()
    stripe_session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    buyer_name = models.CharField(max_length=200, blank=True)
    buyer_email = models.EmailField(blank=True)
    shipping_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    courier = models.CharField(max_length=100, blank=True)
    tracking_url = models.URLField('tracking link', blank=True)
    refund_pence = models.PositiveIntegerField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    objects = OrderQuerySet.as_manager()

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.artwork} ({OrderStatus(self.status).label})'

    def mark_paid(self, buyer_name: str, buyer_email: str, shipping_address: str) -> None:
        self.status = OrderStatus.PAID
        self.paid_at = timezone.now()
        self.buyer_name = buyer_name
        self.buyer_email = buyer_email
        self.shipping_address = shipping_address
        self.save()
        self.artwork.mark_sold()

    def mark_shipped(self, courier: str = '', tracking_url: str = '') -> None:
        if self.status != OrderStatus.PAID:
            return
        self.status = OrderStatus.SHIPPED
        self.shipped_at = timezone.now()
        self.courier = courier
        self.tracking_url = tracking_url
        self.save(update_fields=['status', 'shipped_at', 'courier', 'tracking_url'])

    @property
    def total_pence(self) -> int:
        return self.amount_pence + self.delivery_pence

    def record_refund(self, pence: int, relist: bool) -> None:
        self.refund_pence = pence
        self.refunded_at = timezone.now()
        if pence >= self.total_pence:
            self.status = OrderStatus.REFUNDED
        self.save(update_fields=['refund_pence', 'refunded_at', 'status'])
        if relist:
            self.artwork.relist()

    def mark_expired(self) -> None:
        if self.status != OrderStatus.PENDING:
            return
        self.status = OrderStatus.EXPIRED
        self.save(update_fields=['status'])
        if self.expires_at:
            self.artwork.release(until=self.expires_at)


class StripeEvent(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.id
