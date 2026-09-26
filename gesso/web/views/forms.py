import json

from django.forms import BaseForm
from django.http import HttpRequest


def json_body(request: HttpRequest) -> dict | None:
    try:
        data = json.loads(request.body)
    except ValueError, UnicodeDecodeError:
        return None
    return data if isinstance(data, dict) else None


def form_errors(form: BaseForm) -> dict[str, str]:
    return {field: errors[0]['message'] for field, errors in form.errors.get_json_data().items()}
