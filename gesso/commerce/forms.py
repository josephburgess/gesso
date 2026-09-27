from decimal import Decimal

from django import forms
from django.utils import timezone
from unfold.widgets import (
    UnfoldAdminDecimalFieldWidget,
    UnfoldAdminEmailInputWidget,
    UnfoldAdminSelectWidget,
    UnfoldAdminSingleDateWidget,
    UnfoldAdminTextareaWidget,
    UnfoldAdminTextInputWidget,
    UnfoldAdminURLInputWidget,
    UnfoldBooleanWidget,
)

from gesso.commerce.models import OrderSource


class ShipForm(forms.Form):
    courier = forms.CharField(max_length=100, required=False, widget=UnfoldAdminTextInputWidget)
    tracking_url = forms.URLField(label='Tracking link', required=False, widget=UnfoldAdminURLInputWidget)
    notify = forms.BooleanField(label='Email the buyer', required=False, initial=True, widget=UnfoldBooleanWidget)


class RefundForm(forms.Form):
    amount = forms.DecimalField(
        label='Amount refunded (£)', max_digits=9, decimal_places=2, min_value=0.01, widget=UnfoldAdminDecimalFieldWidget
    )
    relist = forms.BooleanField(label='Put the work back on sale', required=False, widget=UnfoldBooleanWidget)

    def __init__(self, *args, total_pence: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.total_pence = total_pence
        self.initial['amount'] = Decimal(total_pence) / 100

    def clean_amount(self):
        pence = int(self.cleaned_data['amount'] * 100)
        if pence > self.total_pence:
            raise forms.ValidationError('That is more than the buyer paid.')
        return pence


class SaleForm(forms.Form):
    price = forms.DecimalField(label='Price (£)', max_digits=9, decimal_places=2, min_value=0, widget=UnfoldAdminDecimalFieldWidget)
    sold_on = forms.DateField(label='Date', initial=timezone.localdate, widget=UnfoldAdminSingleDateWidget)
    source = forms.ChoiceField(
        label='Where', choices=[c for c in OrderSource.choices if c[0] != OrderSource.ONLINE], widget=UnfoldAdminSelectWidget
    )
    venue = forms.CharField(max_length=200, required=False, help_text='For example the gallery or fair.', widget=UnfoldAdminTextInputWidget)
    buyer_name = forms.CharField(max_length=200, required=False, widget=UnfoldAdminTextInputWidget)
    buyer_email = forms.EmailField(required=False, widget=UnfoldAdminEmailInputWidget)
    notes = forms.CharField(required=False, widget=UnfoldAdminTextareaWidget)
    to_deliver = forms.BooleanField(
        label='Still needs delivering', required=False, help_text='Adds it to Orders to ship.', widget=UnfoldBooleanWidget
    )

    def __init__(self, *args, price_pence: int | None, **kwargs):
        super().__init__(*args, **kwargs)
        if price_pence is not None:
            self.initial['price'] = Decimal(price_pence) / 100
