from gesso.content.models import SiteContent


def test_load_is_a_singleton(db):
    first = SiteContent.load()
    first.statement = "Hello"
    first.save()

    assert SiteContent.load().statement == "Hello"
    assert SiteContent.objects.count() == 1
