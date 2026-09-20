from django.core.mail import EmailMessage
from django.db import transaction

from gesso.content.models import SiteContent
from gesso.enquiries.forms import EnquiryForm
from gesso.enquiries.models import Enquiry


def submit_enquiry(form: EnquiryForm) -> Enquiry:
    enquiry = form.save()
    transaction.on_commit(lambda: notify(enquiry), robust=True)
    return enquiry


def notify(enquiry: Enquiry) -> None:
    recipient = SiteContent.load().notification_email
    if not recipient:
        return
    about = f' about {enquiry.artwork.title}' if enquiry.artwork else ''
    EmailMessage(
        subject=f'New enquiry from {enquiry.name}{about}',
        body=f'{enquiry.message}\n\n{enquiry.name} <{enquiry.email}>',
        to=[recipient],
        reply_to=[enquiry.email],
    ).send()
