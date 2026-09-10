from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from inertia import render

from gesso.artworks.models import Artwork

from . import props


@require_GET
def home(request):
    return render(request, "Home")


@require_GET
def work_index(request):
    artworks = Artwork.objects.published().prefetch_related("images")
    return render(request, "Work/Index", {"artworks": [props.artwork_tile(a) for a in artworks]})


@require_GET
def work_show(request, slug):
    artwork = get_object_or_404(Artwork.objects.published(), slug=slug)
    return render(request, "Work/Show", {"artwork": props.artwork_detail(artwork)})
