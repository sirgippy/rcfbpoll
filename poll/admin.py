from django.contrib import admin
from .models import User, UserRole, Team, Poll, Ballot, BallotEntry

admin.site.register(User)
admin.site.register(UserRole)
admin.site.register(Team)
admin.site.register(Poll)
admin.site.register(Ballot)
admin.site.register(BallotEntry)
