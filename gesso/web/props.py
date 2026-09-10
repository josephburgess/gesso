from django.urls import reverse


def _cover(artwork):
    images = artwork.images.all()
    return images[0].original.url if images else None


def artwork_tile(artwork):
    return {
        "title": artwork.title,
        "year": artwork.year,
        "href": reverse("work_show", args=[artwork.slug]),
        "cover": _cover(artwork),
    }


def artwork_detail(artwork):
    return {
        "title": artwork.title,
        "year": artwork.year,
        "cover": _cover(artwork),
    }
