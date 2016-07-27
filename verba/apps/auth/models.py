from django.utils.crypto import salted_hmac


class VerbaUser(object):
    """
    Authenticated user, similar to the Django one.

    The built-in Django `AbstractBaseUser` sadly depends on a few tables and
    cannot be used without a datbase so we had to create a custom one.
    """

    def __init__(self, pk, token, user_data={}):
        self.pk = pk
        self.is_active = True

        self.token = token
        self.user_data = user_data

    @property
    def name(self):
        return self.user_data.get('name')

    def save(self, *args, **kwargs):
        pass

    def is_authenticated(self, *args, **kwargs):
        return True

    def get_session_auth_hash(self):
        """
        Return an HMAC of the token field.
        """
        key_salt = "auth.models.VerbaUser.get_session_auth_hash"
        return salted_hmac(key_salt, self.token).hexdigest()


class VerbaAnonymousUser(object):
    """
    Anonymous non-authenticated user, similar to the Django one.

    The built-in Django `AnonymousUser` sadly depends on a few tables and
    gives several warnings when used without a database so we had to create a
    custom one.
    """

    def is_authenticated(self, *args, **kwargs):
        return False
