from decimal import Decimal
from typing import cast

from django import forms
from unfold.widgets import UnfoldAdminDecimalFieldWidget

from gesso.artworks.models import FOR_SALE_STATUSES, Artwork, ArtworkStatus


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
        if self.instance.status != ArtworkStatus.RESERVED:
            status = cast(forms.ChoiceField, self.fields['status'])
            status.choices = [c for c in ArtworkStatus.choices if c[0] != ArtworkStatus.RESERVED]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('status') in FOR_SALE_STATUSES and cleaned.get('price') is None:
            self.add_error('price', 'A work for sale needs a price.')
        return cleaned

    def save(self, commit=True):
        self.instance.height_mm = int(self.cleaned_data['height_cm'] * 10)
        self.instance.width_mm = int(self.cleaned_data['width_cm'] * 10)
        price = self.cleaned_data['price']
        self.instance.price_pence = int(price * 100) if price is not None else None
        return super().save(commit)
