from django.db import transaction

from gesso.content.mail import send_templated
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
    send_templated('enquiry_alert', {'enquiry': enquiry}, to=[recipient], reply_to=[enquiry.email])
