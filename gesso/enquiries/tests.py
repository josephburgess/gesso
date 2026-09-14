from django.urls import reverse

from gesso.enquiries.models import Enquiry


def test_opening_an_enquiry_marks_it_read(admin_client):
    enquiry = Enquiry.objects.create(name='A', email='a@example.com', message='Hi')

    admin_client.get(reverse('admin:enquiries_enquiry_change', args=[enquiry.pk]))

    enquiry.refresh_from_db()
    assert enquiry.read_at is not None
