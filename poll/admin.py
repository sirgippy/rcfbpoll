from django.contrib import admin
from .models import User, Team, Poll, Ballot, BallotEntry

admin.site.register(User)
admin.site.register(Team)
admin.site.register(Poll)
admin.site.register(Ballot)
admin.site.register(BallotEntry)
