from django.urls import path

from gesso.web.views import about, checkout, contact, home, work

urlpatterns = [
    path('', home.page, name='home'),
    path('work', work.index, name='work'),
    path('work/<slug:slug>', work.show, name='work_show'),
    path('about', about.page, name='about'),
    path('contact', contact.page, name='contact'),
    path('work/<slug:slug>/checkout', checkout.start, name='checkout'),
    path('checkout/success', checkout.success, name='checkout_success'),
]
