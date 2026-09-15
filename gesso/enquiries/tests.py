from django.urls import reverse

from gesso.content.models import SiteContent
from gesso.enquiries.forms import EnquiryForm
from gesso.enquiries.models import Enquiry
from gesso.enquiries.services import submit_enquiry


def _form(**overrides):
    form = EnquiryForm({'name': 'A', 'email': 'a@example.com', 'message': 'Hi'} | overrides)
    assert form.is_valid()
    return form


def test_submit_enquiry_emails_the_studio(db, mailoutbox, django_capture_on_commit_callbacks):
    content = SiteContent.load()
    content.notification_email = 'studio@example.com'
    content.save()

    with django_capture_on_commit_callbacks(execute=True):
        submit_enquiry(_form())

    [mail] = mailoutbox
    assert mail.to == ['studio@example.com']
    assert mail.reply_to == ['a@example.com']


def test_submit_enquiry_without_recipient_sends_nothing(db, mailoutbox, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        submit_enquiry(_form())

    assert mailoutbox == []


def test_name_newlines_are_collapsed(db):
    assert _form(name='A\nB').cleaned_data['name'] == 'A B'


def test_opening_an_enquiry_marks_it_read(admin_client):
    enquiry = Enquiry.objects.create(name='A', email='a@example.com', message='Hi')

    admin_client.get(reverse('admin:enquiries_enquiry_change', args=[enquiry.pk]))

    enquiry.refresh_from_db()
    assert enquiry.read_at is not None
