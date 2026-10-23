from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """Patients and doctors sign in with their e-mail, the admin with a username."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if not username or password is None:
            return None
        candidates = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username))
        for user in candidates:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        # Run the hasher once to keep timing similar when the user doesn't exist.
        if not candidates:
            User().set_password(password)
        return None
