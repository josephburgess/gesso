from inertia import share

from gesso.web.props import site_props


def share_site(get_response):
    def middleware(request):
        share(request, site=site_props(request.path))
        return get_response(request)

    return middleware
