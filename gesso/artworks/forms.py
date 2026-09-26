from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from unfold.forms import PaginationInlineFormSet
from unfold.widgets import UnfoldAdminDecimalFieldWidget

from gesso.artworks.models import Artwork, ArtworkStatus


class ArtworkAdminForm(forms.ModelForm):
    height_cm = forms.DecimalField(max_digits=6, decimal_places=1, min_value=0, widget=UnfoldAdminDecimalFieldWidget)
    width_cm = forms.DecimalField(max_digits=6, decimal_places=1, min_value=0, widget=UnfoldAdminDecimalFieldWidget)
    price = forms.DecimalField(
        label='Price (£)', max_digits=9, decimal_places=2, min_value=0, required=False, widget=UnfoldAdminDecimalFieldWidget
    )

    class Meta:
        model = Artwork
        exclude = ('height_mm', 'width_mm', 'price_pence')  # noqa: DJ006

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
        if cleaned.get('featured_order') and not cleaned.get('is_published'):
            self.add_error('featured_order', 'Only published works can go on the home page.')
        return cleaned

    def save(self, commit=True):
        self.instance.height_mm = int(self.cleaned_data['height_cm'] * 10)
        self.instance.width_mm = int(self.cleaned_data['width_cm'] * 10)
        price = self.cleaned_data['price']
        self.instance.price_pence = int(price * 100) if price is not None else None
        return super().save(commit)


class ArtworkImageFormSet(PaginationInlineFormSet):
    def clean(self):
        super().clean()
        kept = [
            form
            for form in self.forms
            if getattr(form, 'cleaned_data', None)
            and form.cleaned_data.get('original')
            and not form.cleaned_data.get('DELETE')
            and not form.cleaned_data.get('is_process')
        ]
        if self.instance.is_published and not kept:
            raise ValidationError('A published work needs at least one image of the finished work. Add one, or untick Published.')
