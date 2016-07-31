from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible


class User(models.Model):
    username = models.CharField(max_length=32)
    primary_affiliation = models.ForeignKey('Team', blank=True, null=True)

    def __str__(self):
        return self.username

    def is_a_voter(self):
        return UserRole.objects.filter(user=self, role='voter').exists()


class UserRole(models.Model):
    user = models.ForeignKey('User')
    role = models.CharField(max_length=20)

    def __str__(self):
        return str(self.user) + ' ' + str(self.role)


class UserSecondaryAffiliations(models.Model):
    user = models.ForeignKey('User')
    team = models.ForeignKey('Team')


@python_2_unicode_compatible
class Team(models.Model):
    handle = models.CharField(max_length=60)
    name = models.CharField(max_length=120)
    conference = models.CharField(max_length=60)
    division = models.CharField(max_length=50)
    use_for_ballot = models.BooleanField()

    def __str__(self):
        return self.name


class Poll(models.Model):
    year = models.IntegerField()
    week = models.CharField(max_length=20)
    open_date = models.DateTimeField()
    close_date = models.DateTimeField()

    def __str__(self):
        return str(self.year) + ' ' + str(self.week)

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

    def __str__(self):
        return str(self.poll) + ' ' + str(self.user)


class BallotEntry(models.Model):
    rank = models.IntegerField()
    ballot = models.ForeignKey('Ballot')
    team = models.ForeignKey('Team')
    rationale = models.TextField()

    def __str__(self):
        return str(self.ballot) + ' ' + str(self.rank) + ' ' + str(self.team)
