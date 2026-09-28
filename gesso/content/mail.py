from email.utils import formataddr, parseaddr

from django.conf import settings
from django.core.mail import EmailMessage
from django.template import engines

from gesso.content.models import SiteContent


def from_email() -> str:
    _, address = parseaddr(settings.DEFAULT_FROM_EMAIL)
    return formataddr((SiteContent.load().site_name, address))


def send_templated(template: str, context: dict, to: list[str], reply_to: list[str] | None = None) -> None:
    engine = engines['email']
    EmailMessage(
        from_email=from_email(),
        subject=engine.get_template(f'{template}_subject.txt').render(context).strip(),
        body=engine.get_template(f'{template}.txt').render(context).rstrip('\n'),
        to=to,
        reply_to=reply_to,
    ).send()
