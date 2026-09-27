from email.utils import formataddr, parseaddr

from django.conf import settings

from gesso.content.models import SiteContent


def from_email() -> str:
    _, address = parseaddr(settings.DEFAULT_FROM_EMAIL)
    return formataddr((SiteContent.load().site_name, address))
