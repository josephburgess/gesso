from inertia import render


def home(request):
    return render(request, 'Home', {'message': 'Hello from Django'})
