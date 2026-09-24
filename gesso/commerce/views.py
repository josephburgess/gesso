from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from gesso.commerce import stripe_client
from gesso.commerce.services import handle_event


@csrf_exempt
@require_POST
def stripe_webhook(request: HttpRequest) -> HttpResponse:
    event = stripe_client.construct_event(request.body, request.headers.get('Stripe-Signature', ''))
    if event is None:
        return HttpResponseBadRequest()
    handle_event(event)
    return HttpResponse()
