import uuid

from django.db import models

from gesso.artworks.models import Artwork


class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PAID = 'paid', 'Paid'
    SHIPPED = 'shipped', 'Shipped'
    EXPIRED = 'expired', 'Expired'


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

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.artwork} ({OrderStatus(self.status).label})'


class StripeEvent(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.id
