from django import forms
from unfold.widgets import UnfoldAdminTextInputWidget, UnfoldAdminURLInputWidget, UnfoldBooleanWidget


class ShipForm(forms.Form):
    courier = forms.CharField(max_length=100, required=False, widget=UnfoldAdminTextInputWidget)
    tracking_url = forms.URLField(label='Tracking link', required=False, widget=UnfoldAdminURLInputWidget)
    notify = forms.BooleanField(label='Email the buyer', required=False, initial=True, widget=UnfoldBooleanWidget)
