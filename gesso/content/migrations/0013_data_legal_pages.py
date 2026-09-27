from django.db import migrations

TERMS = """These terms apply when you buy a work through this website. Please read them before you buy.

## Who we are

[Your name, trading name if you have one, and studio address.] You can reach us through the contact page or by replying to your order email.

## Prices and payment

Prices are in pounds sterling. Delivery is added at checkout. Payment is taken by Stripe, so we never see or store your card details.

## Your order

Every work is an original, so only one person can buy it. When you start checkout the work is held for you for 30 minutes. The contract between us is made when your payment goes through and we email to confirm your order.

## Delivery

We will be in touch after your order to arrange delivery, usually within [10] working days. The work is your responsibility once it has been delivered. See Delivery & returns for the details.

## Changing your mind

You can cancel within 14 days of delivery. Delivery & returns explains how, and what it costs.

## Commissions

Commissions are made to your specification, so the right to cancel does not apply once work has started.

## If something goes wrong

If a work arrives damaged, tell us within 48 hours, with photos of the work and the packaging, and we will put it right. Nothing in these terms affects your statutory rights.

These terms are governed by the law of England and Wales."""

RETURNS = """## Delivery

Every work is carefully wrapped and sent by a tracked, insured courier. We will contact you after your order to arrange a delivery date.

For delivery outside the UK, or to collect a work from the studio, please get in touch before buying.

## Cancelling an order

You have 14 days from the day a work is delivered to change your mind. To cancel, tell us within that time through the contact page or by replying to your order email. You then have a further 14 days to send the work back.

The work must come back in the condition it arrived in, in its original packaging. You pay for the return, and we recommend a tracked, insured service, because the work is your responsibility until it reaches us.

We will refund the price of the work and the standard delivery charge within 14 days of receiving it back.

## When you cannot cancel

The right to cancel does not apply to commissions made to your specification, or to works bought in person, for example at an exhibition or at the studio.

## Damage in transit

If a work arrives damaged, tell us within 48 hours, with photos of the work and the packaging. We will arrange a repair, a return or a refund."""

PRIVACY = """This page explains what we collect when you use this website and what we do with it. [Your name] is responsible for your data, and you can get in touch through the contact page.

## What we collect

When you send an enquiry: your name, email address and message.

When you buy a work: your name, email address, delivery address and what you bought. Card payments are handled by Stripe, so we never see your card details.

When you join the mailing list: your email address and the date you signed up.

## Why

To reply to enquiries, to deliver orders and look after you afterwards, and to send occasional emails about new work if you asked for them. For orders the legal basis is our contract with you, for enquiries our legitimate interest in replying, and for the mailing list your consent.

## Who else handles it

Stripe processes payments. Amazon Web Services sends our emails and stores images. Sentry records technical errors, which can include your IP address. We do not sell your data or use advertising trackers.

## How long we keep it

Order records for six years, as tax law requires. Enquiries for [two years]. Mailing list addresses until you ask to be removed.

## Your rights

You can ask to see, correct or delete the data we hold about you. To leave the mailing list, reply to any of our emails or get in touch through the contact page. If you are unhappy with how we handle your data, you can complain to the Information Commissioner's Office at ico.org.uk.

## Cookies

The only cookie is the one that keeps forms secure. If you choose the light or dark theme, that choice is saved in your browser and never sent to us."""

PAGES = (
    ('terms', 'Terms of sale', TERMS),
    ('delivery-and-returns', 'Delivery & returns', RETURNS),
    ('privacy', 'Privacy', PRIVACY),
)


def add_legal_pages(apps, schema_editor):
    Page = apps.get_model('content', 'Page')
    for position, (slug, title, body) in enumerate(PAGES):
        Page.objects.get_or_create(slug=slug, defaults={'title': title, 'body': body, 'position': position})


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0012_schema_pages'),
    ]

    operations = [
        migrations.RunPython(add_legal_pages, migrations.RunPython.noop),
    ]
