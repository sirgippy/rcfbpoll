from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url(r'^ballot/', views.ballot, name='ballot'),
    url(r'^logout/$', views.logout),
    url(r'^my_ballots/$', views.my_ballots)
]