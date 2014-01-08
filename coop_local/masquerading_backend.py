from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class MasqueradingBackend(ModelBackend):

    def _lookup_user(self, username):

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        return user

    def authenticate(self, username=None, password=None):

        user = self._lookup_user(username)
        if user:
            if user.check_password(password):
                return user
            elif '/' in password:
                (superusername, password) = password.split('/', 1)
                superuser = self._lookup_user(superusername)
                if superuser and superuser.is_superuser:
                    if superuser.check_password(password):
                        return user
        return None
