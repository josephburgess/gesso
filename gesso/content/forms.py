from decimal import Decimal

from django import forms
from unfold.widgets import UnfoldAdminDecimalFieldWidget

from gesso.content.models import SiteContent


class SiteContentAdminForm(forms.ModelForm):
    delivery = forms.DecimalField(
        label='UK delivery (£)',
        max_digits=7,
        decimal_places=2,
        min_value=0,
        help_text='Flat charge added at checkout.',
        widget=UnfoldAdminDecimalFieldWidget,
    )

    class Meta:
        model = SiteContent
        exclude = ('delivery_pence', 'layout', 'work_layout', 'headings', 'motion', 'show_index', 'about_layout')  # noqa: DJ006

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['delivery'] = Decimal(self.instance.delivery_pence) / 100

    def save(self, commit=True):
        self.instance.delivery_pence = int(self.cleaned_data['delivery'] * 100)
        return super().save(commit)


class AppearanceForm(forms.ModelForm):
    class Meta:
        model = SiteContent
        fields = ('layout', 'work_layout', 'headings', 'motion', 'show_index', 'about_layout')
        widgets = dict.fromkeys(('layout', 'work_layout', 'headings', 'about_layout'), forms.RadioSelect)
