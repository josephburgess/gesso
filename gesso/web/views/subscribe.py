from django.http import HttpRequest, HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from gesso.enquiries.forms import SubscribeForm
from gesso.enquiries.models import Subscriber
from gesso.web.views.forms import form_errors, json_body

THANKS = "Thanks, you're on the list."


@require_POST
@ratelimit(key='ip', rate='5/h', block=False)
def subscribe(request: HttpRequest) -> JsonResponse | HttpResponseBadRequest:
    if getattr(request, 'limited', False):
        return JsonResponse({'errors': {'email': 'Too many sign-ups from here. Please try again in an hour.'}}, status=429)
    if (data := json_body(request)) is None:
        return HttpResponseBadRequest()
    form = SubscribeForm(data)
    if not form.is_valid():
        return JsonResponse({'errors': form_errors(form)}, status=400)
    if not form.is_spam():
        Subscriber.objects.get_or_create(email=form.cleaned_data['email'])
    return JsonResponse({'message': THANKS})
