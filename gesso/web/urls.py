from django.urls import path

from gesso.web.views import about, contact, home, work

urlpatterns = [
    path('', home.page, name='home'),
    path('work', work.index, name='work'),
    path('work/<slug:slug>', work.show, name='work_show'),
    path('about', about.page, name='about'),
    path('contact', contact.page, name='contact'),
]
