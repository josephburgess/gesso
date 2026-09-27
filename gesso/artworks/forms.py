from decimal import Decimal

from django import forms
from django.db import transaction
from django.db.models import Q
from unfold.widgets import UnfoldAdminDecimalFieldWidget, UnfoldAdminSelectWidget

from gesso.artworks.models import Artwork, ArtworkImage, ArtworkStatus, FrameColour, RoomScene


class PositionedForm(forms.ModelForm):
    def has_changed(self) -> bool:
        if self.instance.pk:
            return super().has_changed()
        return bool(set(self.changed_data) - {'position'})


class ArtworkAdminForm(forms.ModelForm):
    height_cm = forms.DecimalField(max_digits=6, decimal_places=1, min_value=0, widget=UnfoldAdminDecimalFieldWidget)
    width_cm = forms.DecimalField(max_digits=6, decimal_places=1, min_value=0, widget=UnfoldAdminDecimalFieldWidget)
    price = forms.DecimalField(
        label='Price (£)', max_digits=9, decimal_places=2, min_value=0, required=False, widget=UnfoldAdminDecimalFieldWidget
    )

    class Meta:
        model = Artwork
        exclude = ('height_mm', 'width_mm', 'price_pence', 'featured_order', 'position')  # noqa: DJ006

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial |= {
                'height_cm': Decimal(self.instance.height_mm) / 10,
                'width_cm': Decimal(self.instance.width_mm) / 10,
                'price': Decimal(self.instance.price_pence) / 100 if self.instance.price_pence is not None else None,
            }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('status') == ArtworkStatus.AVAILABLE and cleaned.get('price') is None:
            self.add_error('price', 'An available work needs a price.')
        if cleaned.get('is_published') and not self._images().filter(is_process=False).exists():
            self.add_error('is_published', 'A published work needs at least one image of the finished work. Add one, or untick Published.')
        return cleaned

    def _pending_ids(self) -> list[int]:
        return [int(pk) for pk in self.data.get('image_ids', '').split(',') if pk.isdigit()]

    def _images(self):
        pending = Q(artwork=None, pk__in=self._pending_ids())
        return ArtworkImage.objects.filter(Q(artwork=self.instance) | pending if self.instance.pk else pending)

    def attach_pending_images(self, artwork: Artwork) -> None:
        ArtworkImage.objects.filter(artwork=None, pk__in=self._pending_ids()).update(artwork=artwork)

    def save(self, commit=True):
        self.instance.height_mm = int(self.cleaned_data['height_cm'] * 10)
        self.instance.width_mm = int(self.cleaned_data['width_cm'] * 10)
        price = self.cleaned_data['price']
        self.instance.price_pence = int(price * 100) if price is not None else None
        return super().save(commit)


class HomePageForm(forms.Form):
    hero = forms.ModelChoiceField(
        Artwork.objects.published(), required=False, empty_label='None', label='Large hero', widget=UnfoldAdminSelectWidget
    )
    second = forms.ModelChoiceField(
        Artwork.objects.published(), required=False, empty_label='None', label='Second work', widget=UnfoldAdminSelectWidget
    )
    studio = forms.TypedMultipleChoiceField(coerce=int, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        featured = {a.featured_order: a for a in Artwork.objects.published().exclude(featured_order=None)}
        photos = ArtworkImage.objects.filter(is_process=True, artwork__is_published=True)
        self.fields['studio'].choices = [(photo.pk, photo.pk) for photo in photos]
        self.initial = {
            'hero': featured.get(1),
            'second': featured.get(2),
            'studio': list(photos.exclude(home_position=None).order_by('home_position').values_list('pk', flat=True)),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('hero') and cleaned.get('hero') == cleaned.get('second'):
            self.add_error('second', 'Choose a different work from the hero.')
        if len(cleaned.get('studio') or []) > 2:
            self.add_error('studio', 'Choose up to two studio photos.')
        return cleaned

    @transaction.atomic
    def save(self) -> None:
        Artwork.objects.exclude(featured_order=None).update(featured_order=None)
        for spot, work in ((1, self.cleaned_data['hero']), (2, self.cleaned_data['second'])):
            if work:
                Artwork.objects.filter(pk=work.pk).update(featured_order=spot)
        ArtworkImage.objects.exclude(home_position=None).update(home_position=None)
        for position, pk in enumerate(self.cleaned_data['studio']):
            ArtworkImage.objects.filter(pk=pk).update(home_position=position)


class WallViewForm(forms.Form):
    scene = forms.ModelChoiceField(RoomScene.objects.all(), empty_label=None, widget=UnfoldAdminSelectWidget)
    frame = forms.ChoiceField(choices=FrameColour.choices, widget=UnfoldAdminSelectWidget)
