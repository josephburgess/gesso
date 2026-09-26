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


class OrderQuerySet(models.QuerySet['Order']):
    def to_ship(self) -> Self:
        return self.filter(status=OrderStatus.PAID)


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artwork = models.ForeignKey(Artwork, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=20, choices=OrderStatus, default=OrderStatus.PENDING)
    amount_pence = models.PositiveIntegerField()
    delivery_pence = models.PositiveIntegerField()
    stripe_session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    buyer_name = models.CharField(max_length=200, blank=True)
    buyer_email = models.EmailField(blank=True)
    shipping_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)

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

    def mark_shipped(self) -> None:
        if self.status != OrderStatus.PAID:
            return
        self.status = OrderStatus.SHIPPED
        self.shipped_at = timezone.now()
        self.save(update_fields=['status', 'shipped_at'])

    def mark_expired(self) -> None:
        if self.status != OrderStatus.PENDING:
            return
        self.status = OrderStatus.EXPIRED
        self.save(update_fields=['status'])
        self.artwork.release(until=self.expires_at)


class StripeEvent(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.id
