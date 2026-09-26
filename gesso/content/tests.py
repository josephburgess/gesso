from gesso.content.forms import SiteContentAdminForm
from gesso.content.models import SiteContent


def test_load_is_a_singleton(db):
    first = SiteContent.load()
    first.statement = 'Hello'
    first.save()

    assert SiteContent.load().statement == 'Hello'
    assert SiteContent.objects.count() == 1


def test_admin_form_edits_delivery_in_pounds(db):
    content = SiteContent.load()
    content.delivery_pence = 8500
    content.save()

    form = SiteContentAdminForm({'site_name': 'Studio', 'delivery': '92.50'}, instance=content)

    assert form.initial['delivery'] == 85
    assert form.is_valid(), form.errors
    assert form.save().delivery_pence == 9250
