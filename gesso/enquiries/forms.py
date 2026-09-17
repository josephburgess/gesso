from django import forms

from gesso.enquiries.models import Enquiry


class EnquiryForm(forms.ModelForm):
    website = forms.CharField(required=False)  # fake field to stop spambots

    class Meta:
        model = Enquiry
        fields = ('name', 'email', 'message')

    def clean_name(self):
        return ' '.join(self.cleaned_data['name'].split())

    def is_spam(self) -> bool:
        return bool(self.cleaned_data.get('website'))
