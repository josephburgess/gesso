from django import forms

from gesso.artworks.models import Artwork
from gesso.enquiries.models import Enquiry


class EnquiryForm(forms.ModelForm):
    website = forms.CharField(required=False)  # fake field to stop spambots
    artwork = forms.ModelChoiceField(Artwork.objects.published(), to_field_name='slug', required=False)

    class Meta:
        model = Enquiry
        fields = ('name', 'email', 'message', 'artwork')

    def clean_name(self):
        return ' '.join(self.cleaned_data['name'].split())

    def is_spam(self) -> bool:
        return bool(self.cleaned_data.get('website'))
