from django.urls import path

from gesso.web import views

urlpatterns = [
    path('', views.home, name='home'),
    path('work', views.work_index, name='work'),
    path('work/<slug:slug>', views.work_show, name='work_show'),
    path("about", views.about, name="about")
]
