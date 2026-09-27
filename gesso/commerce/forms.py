from decimal import Decimal

from django import forms
from unfold.widgets import UnfoldAdminDecimalFieldWidget, UnfoldAdminTextInputWidget, UnfoldAdminURLInputWidget, UnfoldBooleanWidget


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
