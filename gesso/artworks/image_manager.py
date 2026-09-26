import json
from typing import Any

from django import forms
from django.contrib.admin import ModelAdmin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Max, QuerySet
from django.forms import modelform_factory
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils.safestring import SafeString
from django.views.decorators.http import require_POST

from gesso.artworks.models import ProcessedImage

PENDING = 'pending'


class ImageManager:
    model: type[ProcessedImage]
    fields: tuple[tuple[str, str], ...]
    name: str
    prefix: str

    def __init__(self, model_admin: ModelAdmin):
        self.model_admin = model_admin

    def owner(self, key: str) -> dict[str, Any]:
        raise NotImplementedError

    def allowed(self, request: HttpRequest, key: str) -> bool:
        return self.model_admin.has_change_permission(request)

    def before_upload(self) -> None:
        pass

    def images(self, key: str) -> QuerySet:
        return self.model.objects.filter(**self.owner(key)).order_by('position', 'pk')

    def tile(self, image: ProcessedImage) -> dict[str, Any]:
        return {'id': image.pk, 'thumb': image.thumbnail_url} | {name: getattr(image, name) for name, _ in self.fields}

    def render(self, key: str = '') -> SafeString:
        upload = reverse(f'admin:{self.name}_upload', kwargs={'key': key} if key else {})
        config = {
            'base': upload.removesuffix('upload/'),
            'tiles': [] if key == PENDING else [self.tile(image) for image in self.images(key)],
            'fields': [{'name': name, 'label': label, 'type': self._input_type(name)} for name, label in self.fields],
        }
        return render_to_string('admin/images/manager.html', {'config': config, 'pending': key == PENDING})

    def urls(self) -> list:
        def view(method, suffix):
            return path(
                f'{self.prefix}{suffix}',
                self.model_admin.admin_site.admin_view(require_POST(method)),
                name=f'{self.name}_{method.__name__}',
            )

        return [
            view(self.upload, 'upload/'),
            view(self.order, 'order/'),
            view(self.update, '<int:pk>/'),
            view(self.replace, '<int:pk>/replace/'),
            view(self.delete, '<int:pk>/delete/'),
        ]

    def upload(self, request: HttpRequest, key: str = '') -> JsonResponse:
        self._check(request, key)
        try:
            file = forms.ImageField().clean(request.FILES.get('file'))
        except ValidationError as error:
            return JsonResponse({'error': error.messages[0]}, status=400)
        self.before_upload()
        last = self.images(key).aggregate(last=Max('position'))['last']
        image = self.model(original=file, position=0 if last is None else last + 1, **self.owner(key))
        image.save()
        return JsonResponse(self.tile(image))

    def replace(self, request: HttpRequest, pk: int, key: str = '') -> JsonResponse:
        self._check(request, key)
        image = get_object_or_404(self.images(key), pk=pk)
        try:
            file = forms.ImageField().clean(request.FILES.get('file'))
        except ValidationError as error:
            return JsonResponse({'error': error.messages[0]}, status=400)
        image.replace(file)
        return JsonResponse(self.tile(image))

    def update(self, request: HttpRequest, pk: int, key: str = '') -> JsonResponse:
        self._check(request, key)
        form_class = modelform_factory(self.model, fields=[name for name, _ in self.fields])
        form = form_class(request.POST, instance=get_object_or_404(self.images(key), pk=pk))
        if not form.is_valid():
            return JsonResponse({'error': next(iter(form.errors.values()))[0]}, status=400)
        return JsonResponse(self.tile(form.save()))

    def delete(self, request: HttpRequest, pk: int, key: str = '') -> JsonResponse:
        self._check(request, key)
        image = get_object_or_404(self.images(key), pk=pk)
        image.delete_files()
        image.delete()
        return JsonResponse({})

    def order(self, request: HttpRequest, key: str = '') -> JsonResponse:
        self._check(request, key)
        images = self.images(key)
        for position, pk in enumerate(json.loads(request.body).get('ids', [])):
            images.filter(pk=pk).update(position=position)
        return JsonResponse({})

    def _check(self, request: HttpRequest, key: str) -> None:
        if not self.allowed(request, key):
            raise PermissionDenied

    def _input_type(self, name: str) -> str:
        return 'checkbox' if self.model._meta.get_field(name).get_internal_type() == 'BooleanField' else 'text'
