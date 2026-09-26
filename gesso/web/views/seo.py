from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_GET


@require_GET
def robots(request: HttpRequest) -> HttpResponse:
    lines = ['User-agent: *', 'Disallow: /admin/', 'Disallow: /checkout/']
    if not settings.NOINDEX:
        lines.append(f'Sitemap: {request.build_absolute_uri(reverse("sitemap"))}')
    return HttpResponse('\n'.join(lines) + '\n', content_type='text/plain')
