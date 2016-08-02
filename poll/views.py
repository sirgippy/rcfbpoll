from django.shortcuts import render, redirect
from .models import Team, Poll, Ballot, User, BallotEntry
from django.db.models import Q
from django.contrib.auth import logout as auth_logout
from django.utils import timezone
from django.http import HttpResponse, HttpResponseBadRequest
import json
from urllib import unquote


def home(request):
    return render(request, 'poll/home.html', {})


def edit_ballot(request, pk):
    ballot = Ballot.objects.get(pk=pk)

    ballot_user = ballot.user
    this_user = User.objects.get(username=request.user.username)
    if not ballot_user == this_user:
        return redirect('/ballot/' + str(pk))

    entries = ballot.ballotentry_set.all().order_by('rank')

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
    teams['other'] = all_teams.filter(~Q(division='FBS'))

    return render(request, 'poll/ballot_editor.html', {'ballot': ballot,
                                                       'entries': entries,
                                                       'teams': teams})


def create_ballot(request, pk):
    poll = Poll.objects.get(pk=pk)
    user = User.objects.get(username=request.user.username)
    new_ballot = Ballot(user=user, poll=poll)
    new_ballot.save()
    return redirect('/edit_ballot/' + str(new_ballot.pk))


def logout(request):
    auth_logout(request)
    return redirect('/')


def not_a_user(request):
    return render(request, 'poll/coming_soon.html', {})


def my_ballots(request):
    if not request.user.is_authenticated():
        return render(request, 'poll/login.html')

    this_user = User.objects.get(username=request.user.username)

    if not this_user.is_a_voter():
        return render(request, 'poll/not_a_voter.html', {})

    open_poll = None
    polls = Poll.objects.all()
    for poll in polls:
        if poll.is_open:
            open_poll = poll

    ballots = Ballot.objects.filter(user=this_user).order_by('-submission_date')

    open_ballot = None
    for ballot in ballots:
        if ballot.is_open:
            open_ballot = ballot

    return render(request, 'poll/my_ballots.html', {'open_poll': open_poll,
                                                    'open_ballot': open_ballot,
                                                    'ballots': ballots})


def save_ballot(request, pk):
    save_ballot_data(request, pk)

    time_saved = timezone.now().strftime('%B %d, %Y %I:%M %p')
    return HttpResponse(
        json.dumps(time_saved),
        content_type="application/json"
    )


def save_ballot_data(request, pk):
    poll_type = request.POST.get('poll_type')
    if poll_type == '(unspecified)':
        poll_type = ''
    overall_rationale = unquote(request.POST.get('overall_rationale'))

    entries = json.loads(request.POST.get('entries'))

    ballot = Ballot.objects.get(pk=pk)
    ballot.poll_type = poll_type
    ballot.overall_rationale = overall_rationale
    ballot.save()

    for entry in entries:
        if BallotEntry.objects.filter(ballot=ballot, rank=entry['rank']).exists():
            ballot_entry = BallotEntry.objects.get(ballot=ballot, rank=entry['rank'])
            ballot_entry.team = Team.objects.get(handle=entry['team'])
            ballot_entry.rationale = unquote(entry['rationale'])
        else:
            ballot_entry = BallotEntry(ballot=ballot,
                                       rank=entry['rank'],
                                       team=Team.objects.get(handle=entry['team']),
                                       rationale=unquote(entry['rationale']))
        ballot_entry.save()

    ballot_entries = BallotEntry.objects.filter(ballot=ballot, rank__gt=len(entries))

    for ballot_entry in ballot_entries:
        ballot_entry.delete()


def submit_ballot(request, pk):
    poll_type = request.POST.get('poll_type')
    if poll_type == '(unspecified)':
        return HttpResponseBadRequest()

    overall_rationale = unquote(request.POST.get('overall_rationale'))

    entries = json.loads(request.POST.get('entries'))

    if not len(entries) == 25:
        return HttpResponseBadRequest()

    teams = []
    for entry in entries:
        team = Team.objects.get(handle=entry['team'])
        if team in teams or not team.use_for_ballot:
            return HttpResponseBadRequest()
        else:
            teams.append(team)

    ballot = Ballot.objects.get(pk=pk)

    user = User.objects.get(username=request.user.username)
    if ballot.user != user:
        return HttpResponseBadRequest()

    poll = ballot.poll
    if poll.is_closed or not poll.is_open:
        return HttpResponseBadRequest()

    if ballot.is_submitted:
        return HttpResponseBadRequest()

    ballot.poll_type = poll_type
    ballot.overall_rationale = overall_rationale
    ballot.submit()
    ballot.save()

    for entry in entries:
        if BallotEntry.objects.filter(ballot=ballot, rank=entry['rank']).exists():
            ballot_entry = BallotEntry.objects.get(ballot=ballot, rank=entry['rank'])
            ballot_entry.team = Team.objects.get(handle=entry['team'])
            ballot_entry.rationale = unquote(entry['rationale'])
        else:
            ballot_entry = BallotEntry(ballot=ballot,
                                       rank=entry['rank'],
                                       team=Team.objects.get(handle=entry['team']),
                                       rationale=unquote(entry['rationale']))
        ballot_entry.save()

    time_saved = timezone.now().strftime('%B %d, %Y %I:%M %p')
    return HttpResponse(
        json.dumps(time_saved),
        content_type="application/json"
    )


def retract_ballot(request, pk):
    ballot = Ballot.objects.get(pk=pk)

    user = User.objects.get(username=request.user.username)

    if ballot.user != user:
        return HttpResponseBadRequest()

    ballot.retract()
    ballot.save()

    return HttpResponse()
