from django.shortcuts import render, redirect
from .models import Team, Poll, Ballot, User, BallotEntry, PollCompare
from django.db.models import Q
from django.contrib.auth import logout as auth_logout
from django.utils import timezone
from django.http import HttpResponse, HttpResponseBadRequest
import json
import os
from urllib import unquote


def home(request):
    polls = Poll.objects.filter(close_date__lt=timezone.now()).order_by('-close_date')
    most_recent_poll = polls[0]

    ranks = PollCompare.objects.filter(poll=most_recent_poll).order_by('rank')
    top25 = ranks[0:25]
    others = ranks[25:]
    up_movers = ranks.order_by('-ppv_diff')[0:5]
    down_movers = ranks.order_by('ppv_diff')[0:5]

    return render(request, 'poll/home.html', {'poll': most_recent_poll,
                                              'top25': top25,
                                              'others': others,
                                              'up_movers': up_movers,
                                              'down_movers': down_movers})


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


def view_ballot(request, pk):
    ballot = Ballot.objects.get(pk=pk)

    this_user = User.objects.get(username=request.user.username)

    if not ballot.is_closed and ballot.user != this_user:
        return HttpResponse(status=403)

    entries = ballot.ballotentry_set.all().order_by('rank')

    return render(request, 'poll/ballot_viewer.html', {'ballot': ballot,
                                                       'entries': entries})


def view_current_poll(request):
    if request.GET.get('year'):
        if Poll.objects.filter(year=request.GET.get('year'), week=request.GET.get('week')).exists():
            poll = Poll.objects.get(year=request.GET.get('year'), week=request.GET.get('week'))
        else:
            poll = Poll.objects.filter(year=request.GET.get('year'),
                                       close_date__lt=timezone.now()).order_by('-close_date')[0]
        return redirect('/poll/' + str(poll.pk) + '/')
    else:
        polls = Poll.objects.filter(close_date__lt=timezone.now()).order_by('-close_date')
        most_recent_poll = polls[0]

        return redirect('/poll/' + str(most_recent_poll.pk) + '/')


def view_poll(request, pk):
    poll = Poll.objects.get(pk=pk)

    ranks = PollCompare.objects.filter(poll=poll).order_by('rank')
    top25 = ranks[0:25]
    others = ranks[25:]
    up_movers = ranks.order_by('-ppv_diff')[0:5]
    down_movers = ranks.order_by('ppv_diff')[0:5]

    years = Poll.objects.filter(close_date__lt=timezone.now()).values_list('year', flat=True).distinct().order_by('-year')
    weeks = Poll.objects.filter(year=poll.year).values_list('week', flat=True).order_by('-close_date')

    return render(request, 'poll/poll_viewer.html', {'poll': poll,
                                                     'top25': top25,
                                                     'others': others,
                                                     'up_movers': up_movers,
                                                     'down_movers': down_movers,
                                                     'years': years,
                                                     'weeks': weeks})


def messenger(request):
    if not request.user.is_staff:
        return HttpResponse('Unauthorized', status=401)
    return render(request, 'poll/messenger.html')


def send_message(request):
    return redirect('/')


def acme(request, challenge):
    responses = os.environ.get('ACME_PAIRS').split(',')
    challenges_and_responses = { x[:43]: x for x in responses }
    return HttpResponse(challenges_and_responses.get(challenge, "Not found!"))