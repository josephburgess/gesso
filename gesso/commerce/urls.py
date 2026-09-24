from django.urls import path

from gesso.commerce import views

urlpatterns = [
    path('webhooks/stripe', views.stripe_webhook, name='stripe_webhook'),
]
