from django.http import HttpRequest, HttpResponse
from inertia import render


def not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    response = render(request, 'NotFound', template_data={'title': 'Page not found'})
    response.status_code = 404
    return response
