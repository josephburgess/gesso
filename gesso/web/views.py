from django.shortcuts import get_object_or_404
from django.urls import reverse
from inertia import render

from gesso.artworks.models import Artwork


def home(request):
    return render(request, 'Home', {'message': 'Hello from Django'})


def work_index(request):
    artworks = [
        {"title": a.title, "year": a.year, "href": reverse("work_show", args=[a.slug])}
        for a in Artwork.objects.published()
    ]
    return render(request, "Work/Index", {"artworks": artworks})


def work_show(request, slug):
    artwork = get_object_or_404(Artwork.objects.published(), slug=slug)
    return render(request, "Work/Show", {"artwork": {"title": artwork.title, "year": artwork.year}})
