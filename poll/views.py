from django.shortcuts import render, redirect
from .models import Team, Poll, Ballot, User, BallotEntry, PollCompare, PollPoints
from django.db.models import Q, Sum
from django.contrib.auth import logout as auth_logout
from django.utils import timezone
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.template.defaultfilters import register
import json
import os
from urllib import unquote
from reddit import message_voters
from collections import defaultdict
from math import ceil
import csv

@register.filter(name='lookup')
def lookup(dict, index):
    if index in dict:
        return dict[index]
    return ''

def home(request):
    polls = Poll.objects.filter(close_date__lt=timezone.now()).order_by('-close_date')
    most_recent_poll = polls[0]

    ranks = PollCompare.objects.filter(poll=most_recent_poll).order_by('rank')
    top25 = ranks[0:25]
    others = ranks[25:]
    up_movers = ranks.order_by('-ppv_diff')[0:5]
    down_movers = ranks.order_by('ppv_diff')[0:5]

    # Tally first-place votes by team
    votes = BallotEntry.objects.filter(ballot__poll=most_recent_poll, rank=1).values('team').annotate(total=Sum('rank'))
    fp_votes = {}
    for vote in votes:
        fp_votes[vote['team']] = vote['total']

    # Find which teams dropped out from last week's poll
    dropped = []
    prev_poll = most_recent_poll.last_week
    if prev_poll is not None:
        prev_top25 = PollCompare.objects.filter(poll=prev_poll).order_by('rank')[0:25]

        teams = []
        for team in top25:
            teams.append(team.team.pk)

        for team in prev_top25:
            if team.team.pk not in teams:
                dropped.append(team)

    return render(request, 'poll/home.html', {'poll': most_recent_poll,
                                              'top25': top25,
                                              'others': others,
                                              'up_movers': up_movers,
                                              'down_movers': down_movers,
                                              'dropped': dropped,
                                              'fp_votes': fp_votes})


def edit_ballot(request, pk):
    if not request.user.is_authenticated():
        return render(request, 'poll/login.html')

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

    if Ballot.objects.filter(user=user, poll=poll).exists():
        ballot = Ballot.objects.get(user=user, poll=poll)
        return redirect('/edit_ballot/' + str(ballot.pk))

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

    if request.user.is_authenticated():
        this_user = User.objects.get(username=request.user.username)

        if not ballot.is_closed and ballot.user != this_user and not request.user.is_staff:
            return HttpResponseForbidden()
    else:
        this_user = None
        if not ballot.is_closed:
            return HttpResponseForbidden()

    entries = ballot.ballotentry_set.all().order_by('rank')

    user_ballots = Ballot.objects.filter(user=ballot.user, submission_date__isnull=False)
    if not request.user.is_authenticated() or ballot.user != this_user:
        user_ballots = user_ballots.filter(poll__close_date__lt=timezone.now())
    years = user_ballots.values_list('poll__year', flat=True).distinct().order_by('-poll__year')
    weeks = user_ballots.filter(poll__year=ballot.year).values_list('poll__week', flat=True).order_by('-poll')

    if ballot.is_closed:
        users = Ballot.objects.filter(poll__year=ballot.year, poll__week=ballot.week).values_list(
            'user__username', flat=True).order_by('user')
    else:
        users = [ballot.user.username]

    return render(request, 'poll/ballot_viewer.html', {'ballot': ballot,
                                                       'entries': entries,
                                                       'years': years,
                                                       'weeks': weeks,
                                                       'users': users})


def show_ballot(request):
    username = request.GET.get('username')
    year = request.GET.get('year')
    week = request.GET.get('week')
    ballot = Ballot.objects.get(user__username=username, poll__year=year, poll__week=week)
    return redirect('/ballot/' + str(ballot.pk) + '/')


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

    if not poll.is_closed and not request.user.is_staff:
        return HttpResponseForbidden()

    ranks = PollCompare.objects.filter(poll=poll).order_by('rank')
    top25 = ranks[0:25]
    others = ranks[25:]
    up_movers = ranks.order_by('-ppv_diff')[0:5]
    down_movers = ranks.order_by('ppv_diff')[0:5]

    # Tally first-place votges by team
    votes = BallotEntry.objects.filter(ballot__poll=poll, rank=1).values('team').annotate(total=Sum('rank'))
    fp_votes = {}
    for vote in votes:
        fp_votes[vote['team']] = vote['total']

    # Find teams dropped from last week's poll
    dropped = []
    prev_poll = poll.last_week
    if prev_poll is not None:
        prev_top25 = PollCompare.objects.filter(poll=prev_poll).order_by('rank')[0:25]

        teams = []
        for team in top25:
            teams.append(team.team.pk)

        for team in prev_top25:
            if team.team.pk not in teams:
                dropped.append(team)

    years = Poll.objects.filter(close_date__lt=timezone.now()).values_list(
        'year', flat=True).distinct().order_by('-year')
    weeks = Poll.objects.filter(year=poll.year).values_list(
        'week', flat=True).order_by('-close_date')

    return render(request, 'poll/poll_viewer.html', {'poll': poll,
                                                     'top25': top25,
                                                     'others': others,
                                                     'up_movers': up_movers,
                                                     'down_movers': down_movers,
                                                     'dropped': dropped,
                                                     'years': years,
                                                     'weeks': weeks,
                                                     'fp_votes': fp_votes})


def messenger(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    return render(request, 'poll/messenger.html')


def send_message(request):
    username = request.user.username
    social = request.user.social_auth.get(provider='reddit')
    access_token = social.extra_data['access_token']
    title = request.POST.get('title')
    body = request.POST.get('message_body')
    if request.POST.get('recipient') == 'Voters':
        message_voters(username, access_token, title, body)
    return HttpResponse()


def acme(request, challenge):
    responses = os.environ.get('ACME_PAIRS').split(',')
    challenges_and_responses = {x[:43]: x for x in responses}
    return HttpResponse(challenges_and_responses.get(challenge, "Not found!"))


def view_poll_ballots(request, pk, page=1):
    poll = Poll.objects.get(pk=pk)

    if not poll.is_closed and not request.user.is_staff:
        return HttpResponseForbidden()

    page = int(page)

    ballot_ids = poll.ballot_set.filter(submission_date__isnull=False).values_list(
        'pk', flat=True).order_by('user')
    num_ballots = ballot_ids.count()

    if page*5 < num_ballots:
        this_page_ballots = ballot_ids[(page-1)*5:page*5]
    else:
        this_page_ballots = ballot_ids[(page-1)*5:num_ballots]

    ballot_entries = BallotEntry.objects.filter(ballot__pk__in=this_page_ballots).values_list(
        'ballot__pk', 'team__pk', 'team__handle', 'team__short_name', 'rank'
    )

    ballot_dict = dict([(ballot_id, i) for i, ballot_id in enumerate(this_page_ballots)])

    rank_dict = defaultdict(lambda: [""]*len(this_page_ballots))

    for (ballot_id, team_id, handle, short_name, rank) in ballot_entries:
        rank_dict[rank][ballot_dict[ballot_id]] = [team_id, handle, short_name]

    rank_list = list(rank_dict.items())

    ballots = Ballot.objects.filter(pk__in=this_page_ballots).order_by('user')

    years = Poll.objects.filter(close_date__lt=timezone.now()).values_list('year', flat=True).distinct().order_by(
        '-year')
    weeks = Poll.objects.filter(year=poll.year, close_date__lt=timezone.now()).values_list('week', flat=True).order_by('-close_date')

    num_pages = int(ceil(num_ballots/5.0))

    pages = []
    if page < 5:
        for i in range(1, page):
            pages.append(i)
        if page >= num_pages - 4:
            for i in range(page, num_pages+1):
                pages.append(i)
        else:
            pages.append(page)
            pages.append(page+1)
            pages.append(page+2)
            pages.append('...')
            pages.append(num_pages)
    elif page >= num_pages - 4:
        pages = [1, '...', page-2, page-1]
        for i in range(page, num_pages+1):
            pages.append(i)
    else:
        pages = [1, '...', page-2, page-1, page, page+1, page+2, '...', num_pages]

    return render(request, 'poll/poll_ballots.html', {'poll': poll,
                                                      'page': page,
                                                      'ballots': ballots,
                                                      'rank_list': rank_list,
                                                      'years': years,
                                                      'weeks': weeks,
                                                      'pages': pages,
                                                      'num_pages': num_pages})


def view_poll_voters(request, pk):
    poll = Poll.objects.get(pk=pk)
    ballots = poll.ballot_set.filter(submission_date__isnull=False).order_by('user__username')

    years = Poll.objects.filter(close_date__lt=timezone.now()).values_list('year', flat=True).distinct().order_by(
        '-year')
    weeks = Poll.objects.filter(year=poll.year).values_list('week', flat=True).order_by('-close_date')

    return render(request, 'poll/poll_voter_view.html', {'ballots': ballots,
                                                         'years': years,
                                                         'weeks': weeks,
                                                         'poll': poll})


def show_voters(request):
    if request.GET.get('year'):
        year = request.GET.get('year')
        week = request.GET.get('week')
        if Poll.objects.filter(year=year, week=week, close_date__lt=timezone.now()).exists():
            poll = Poll.objects.get(year=year, week=week)
        else:
            poll = Poll.objects.filter(year=year, close_date__lt=timezone.now()).order_by('-close_date')[0]
    else:
        poll = Poll.objects.filter(close_date__lt=timezone.now()).order_by('-close_date')[0]
    return redirect('/poll/' + str(poll.pk) + '/voters/')


def show_ballots(request):
    if request.GET.get('year'):
        year = request.GET.get('year')
        week = request.GET.get('week')
        if Poll.objects.filter(year=year, week=week, close_date__lt=timezone.now()).exists():
            poll = Poll.objects.get(year=year, week=week)
        else:
            poll = Poll.objects.filter(year=year, close_date__lt=timezone.now()).order_by('-close_date')[0]
    else:
        poll = Poll.objects.filter(close_date__lt=timezone.now()).order_by('-close_date')[0]
    return redirect('/poll/' + str(poll.pk) + '/ballots/')


def export_ballots(request, pk):
    poll = Poll.objects.get(pk=pk)

    if not poll.is_closed and not request.user.is_staff:
        return HttpResponseForbidden()

    ballot_ids = poll.ballot_set.filter(submission_date__isnull=False).values_list('pk', flat=True).order_by('user')

    ballot_entries = BallotEntry.objects.filter(ballot__pk__in=ballot_ids).values_list(
        'ballot__pk', 'team__short_name', 'rank'
    )

    ballot_dict = dict([(ballot_id, i) for i, ballot_id in enumerate(ballot_ids)])

    rank_dict = defaultdict(lambda: [""] * len(ballot_ids))

    for (ballot_id, short_name, rank) in ballot_entries:
        rank_dict[rank][ballot_dict[ballot_id]] = short_name

    rank_list = list(rank_dict.items())
    rank_list[:] = [[rank[0]] + rank[1] for rank in rank_list]

    usernames = Ballot.objects.filter(pk__in=ballot_ids).values_list('user__username', flat=True).order_by('user')
    types = Ballot.objects.filter(pk__in=ballot_ids).values_list('poll_type', flat=True).order_by('user')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ballots.csv"'

    writer = csv.writer(response)
    writer.writerow(['User'] + [username for username in usernames])
    writer.writerow(['Type'] + [poll_type for poll_type in types])
    for rank in rank_list:
        writer.writerow([unicode(s).encode('utf-8') for s in rank])

    return response


def about(request):
    return render(request, 'poll/about.html')


def view_team_reasons(request, poll_pk, team_pk):
    poll = Poll.objects.get(pk=poll_pk)
    team = Team.objects.get(pk=team_pk)

    if not poll.is_closed and not request.user.is_staff:
        return HttpResponseForbidden()

    ballot_entries = BallotEntry.objects.filter(ballot__poll=poll,
                                                ballot__submission_date__isnull=False,
                                                team=team).order_by('rank', 'ballot__user__username')

    return render(request, 'poll/team_reasons.html', {'entries': ballot_entries,
                                                      'team': team,
                                                      'poll': poll,
                                                      })
