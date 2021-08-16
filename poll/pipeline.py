from .models import User
from social_core.pipeline.partial import partial


@partial
def check_for_user(user, *args, **kwargs):
    if not User.objects.filter(username=user.username).exists():
        new_user = User(username=user.username)
        new_user.save()
    return
