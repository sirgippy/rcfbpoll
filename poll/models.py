from __future__ import unicode_literals

from django.db import models
from django.utils import timezone


class User(models.Model):
    username = models.CharField(max_length=32)
    primary_affiliation = models.ForeignKey('Team', blank=True, null=True)

    def __unicode__(self):
        return self.username

    def is_a_voter(self):
        return UserRole.objects.filter(user=self, role='voter').exists()

    class Meta:
        ordering = ('username',)


class UserRole(models.Model):
    user = models.ForeignKey('User')
    role = models.CharField(max_length=20)

    def __unicode__(self):
        return unicode(self.user) + ' ' + unicode(self.role)


class UserSecondaryAffiliations(models.Model):
    user = models.ForeignKey('User')
    team = models.ForeignKey('Team')


class Team(models.Model):
    handle = models.CharField(max_length=60)
    name = models.CharField(max_length=120)
    conference = models.CharField(max_length=60)
    division = models.CharField(max_length=50)
    use_for_ballot = models.BooleanField()
    short_name = models.CharField(max_length=60)
    ordering = ['name']

    def __unicode__(self):
        return unicode(self.name)


class Poll(models.Model):
    year = models.IntegerField()
    week = models.CharField(max_length=20)
    open_date = models.DateTimeField()
    close_date = models.DateTimeField()
    last_week = models.ForeignKey('Poll', blank=True, null=True)

    def __unicode__(self):
        return unicode(self.year) + ' ' + unicode(self.week)

    @property
    def is_open(self):
        return self.open_date < timezone.now() < self.close_date

    @property
    def is_closed(self):
        return self.close_date < timezone.now()

    class Meta:
        ordering = ('close_date',)


class Ballot(models.Model):
    user = models.ForeignKey('User')
    poll = models.ForeignKey('Poll')
    submission_date = models.DateTimeField(blank=True, null=True)
    poll_type = models.CharField(max_length=10,
                                 blank=True,
                                 null=True)
    overall_rationale = models.TextField(blank=True, null=True)

    def submit(self):
        self.submission_date = timezone.now()
        self.save()

    def retract(self):
        self.submission_date = None
        self.save()

    @property
    def is_submitted(self):
        return self.submission_date is not None

    @property
    def year(self):
        return self.poll.year

    @property
    def week(self):
        return self.poll.week

    @property
    def open_date(self):
        return self.poll.open_date

    @property
    def close_date(self):
        return self.poll.close_date

    @property
    def is_open(self):
        return self.poll.is_open

    @property
    def is_closed(self):
        return self.poll.is_closed

    def __unicode__(self):
        return unicode(self.poll) + ' ' + unicode(self.user)


class BallotEntry(models.Model):
    rank = models.IntegerField()
    ballot = models.ForeignKey('Ballot')
    team = models.ForeignKey('Team')
    rationale = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return unicode(self.ballot) + ' ' + unicode(self.rank) + ' ' + unicode(self.team)


class PollPoints(models.Model):
    id = models.BigIntegerField(primary_key=True)
    poll = models.ForeignKey(Poll, on_delete=models.DO_NOTHING)
    team = models.ForeignKey(Team, on_delete=models.DO_NOTHING)
    points = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'poll_pollpoints'


class PollCompare(models.Model):
    id = models.BigIntegerField(primary_key=True)
    poll = models.ForeignKey(Poll, on_delete=models.DO_NOTHING)
    team = models.ForeignKey(Team, on_delete=models.DO_NOTHING)
    rank = models.IntegerField()
    points = models.IntegerField()
    ppv = models.FloatField()
    rank_diff = models.IntegerField(blank=True, null=True)
    ppv_diff = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'poll_pollcompare'
