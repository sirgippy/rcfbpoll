from django.shortcuts import render, redirect
from .models import Team, Poll, Ballot, User
from django.db.models import Q
from django.contrib.auth import logout as auth_logout


def home(request):
    return render(request, 'poll/home.html', {})


def ballot(request):
    all_teams = Team.objects.filter(use_for_ballot=True)
    teams = dict()
    teams['acc'] = all_teams.filter(conference='ACC')
    teams['bigten'] = all_teams.filter(conference='Big Ten')
    teams['big12'] = all_teams.filter(conference='Big 12')
    teams['pac12'] = all_teams.filter(conference='Pac-12')
    teams['sec'] = all_teams.filter(conference='SEC')
    teams['ind'] = all_teams.filter(conference='D1 Independents')
    teams['aac'] = all_teams.filter(conference='American')
    teams['cusa'] = all_teams.filter(conference='Conference USA')
    teams['mac'] = all_teams.filter(conference='MAC')
    teams['mwc'] = all_teams.filter(conference='Mountain West')
    teams['sbc'] = all_teams.filter(conference='Sun Belt')
    teams['other'] = all_teams.filter(~Q(division= 'FBS'))
    return render(request, 'poll/ballot_editor.html', {'teams': teams})


def logout(request):
    auth_logout(request)
    return redirect('/')


def not_a_user(request):
    return render(request, 'poll/coming_soon.html', {})


def my_ballots(request):
    this_user = User.objects.filter(username=request.user.username)[0]

    if not this_user.is_a_voter():
        return render(request, 'poll/not_a_voter.html', {})

    polls = Team.objects.all()
    ballots = Ballot.objects.filter(user=this_user)

    return render(request, 'poll/my_ballots.html', {'polls': polls, 'ballots': ballots})
