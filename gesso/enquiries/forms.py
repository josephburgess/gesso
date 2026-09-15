from django import forms

from gesso.enquiries.models import Enquiry


class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ('name', 'email', 'message')

    def clean_name(self):
        return ' '.join(self.cleaned_data['name'].split())
