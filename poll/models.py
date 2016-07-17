from __future__ import unicode_literals

from django.db import models
from django.utils import timezone


class User(models.Model):
    username = models.CharField(max_length=32)
    primary_affiliation = models.ForeignKey('Team', blank=True, null=True)

    def __str__(self):
        return self.username


class UserSecondaryAffiliations(models.Model):
    user = models.ForeignKey('User')
    team = models.ForeignKey('Team')


class Team(models.Model):
    handle = models.CharField(max_length=40)
    name = models.CharField(max_length=80)
    conference = models.CharField(max_length=20)
    division = models.CharField(max_length=6)
    use_for_ballot = models.BooleanField()

    def __str__(self):
        return self.name


class Poll(models.Model):
    year = models.IntegerField()
    week = models.CharField(max_length=20)
    open_date = models.DateTimeField()
    close_date = models.DateTimeField()

    def __str__(self):
        return str(self.year) + ' ' + self.week


class Ballot(models.Model):
    user = models.ForeignKey('User')
    poll = models.ForeignKey('Poll')
    submission_date = models.DateTimeField(blank=True, null=True)
    poll_type = models.CharField(max_length=10,
                                 blank=True,
                                 null=True)
    overall_rationale = models.TextField()

    def submit(self):
        self.submission_date = timezone.now()
        self.save()

    def __str__(self):
        return self.poll + ' ' + self.user


class BallotEntry(models.Model):
    rank = models.IntegerField()
    ballot = models.ForeignKey('Ballot')
    team = models.ForeignKey('Team')
    rationale = models.TextField()

    def __str__(self):
        return self.ballot + ' ' + self.rank
