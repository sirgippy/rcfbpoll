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
    url(r'^edit_ballot/(?P<pk>\d+)/retract_ballot/$', views.retract_ballot),
    url(r'^ballot/(?P<pk>\d+)/$', views.view_ballot),
    url(r'^show_ballot/$', views.show_ballot),
    url(r'^poll/(?P<pk>\d+)/$', views.view_poll),
    url(r'^poll/$', views.view_current_poll),
    url(r'^poll/(?P<pk>\d+)/voters/$', views.view_poll_voters),
    url(r'^show_voters/$', views.show_voters),
    url(r'^poll/(?P<pk>\d+)/ballots/$', views.view_poll_ballots),
    url(r'^poll/(?P<pk>\d+)/export_ballots/$', views.export_ballots),
    url(r'^poll/(?P<pk>\d+)/ballots/(?P<page>\d+)/$', views.view_poll_ballots),
    url(r'^show_ballots/$', views.show_ballots),
    url(r'^messenger/$', views.messenger),
    url(r'^messenger/send_message/$', views.send_message),
    url(r'^about/$', views.about),
    url(r'^poll/(?P<poll_pk>\d+)/team/(?P<team_pk>\d+)/$', views.view_team_reasons),
    url(r'^.well-known/acme-challenge/(?P<challenge>[\w_\-]{43})$', views.acme, name='acme'),
]
