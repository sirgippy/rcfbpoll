from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url(r'^edit_ballot/(?P<pk>\d+)/$', views.edit_ballot, name='edit_ballot'),
    url(r'^logout/$', views.logout),
    url(r'^my_ballots/$', views.my_ballots),
    url(r'^create_ballot/(?P<pk>\d+)/$', views.create_ballot, name='create_ballot'),
    url(r'^edit_ballot/(?P<pk>\d+)/save_ballot/$', views.save_ballot, name='save_ballot'),
    url(r'^edit_ballot/(?P<pk>\d+)/submit_ballot/$', views.submit_ballot, name='submit_ballot'),
]
