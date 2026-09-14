from django import forms

from gesso.enquiries.models import Enquiry


class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ('name', 'email', 'message')
