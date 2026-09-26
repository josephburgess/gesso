from django.urls import reverse
from django.utils import timezone

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


def test_admin_lists_unread_enquiries_first(admin_client):
    read = Enquiry.objects.create(name='Read Rita', email='r@example.com', message='Hi')
    Enquiry.objects.filter(pk=read.pk).update(read_at=timezone.now())
    Enquiry.objects.create(name='Unread Una', email='u@example.com', message='Hi')

    html = admin_client.get('/admin/enquiries/enquiry/').content.decode()

    assert html.index('Unread Una') < html.index('Read Rita')


def test_admin_offers_a_reply_by_email(admin_client, make_artwork):
    enquiry = Enquiry.objects.create(
        name='Ann', email='ann@example.com', message='Is it still available?', artwork=make_artwork(title='Ferry Light')
    )

    html = admin_client.get(f'/admin/enquiries/enquiry/{enquiry.pk}/change/').content.decode()

    assert 'mailto:ann@example.com?subject=Re%3A%20Ferry%20Light' in html
    assert 'Is%20it%20still%20available' in html
