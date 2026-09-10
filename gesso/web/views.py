from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET
from inertia import render

from gesso.artworks.models import Artwork


def _cover(artwork):
    images = artwork.images.all()
    return images[0].original.url if images else None

@require_GET
def home(request):
    return render(request, 'Home', {'message': 'Hello from Django'})

@require_GET
def work_index(request):
    artworks = [
        {
            "title": a.title,
            "year": a.year,
            "href": reverse("work_show", args=[a.slug]),
            "cover": _cover(a),
        }
        for a in Artwork.objects.published().prefetch_related("images")
    ]
    return render(request, "Work/Index", {"artworks": artworks})


@require_GET
def work_show(request, slug):
    artwork = get_object_or_404(Artwork.objects.published(), slug=slug)
    return render(
        request,
        "Work/Show",
        {"artwork": {"title": artwork.title, "year": artwork.year, "cover": _cover(artwork)}},
    )

