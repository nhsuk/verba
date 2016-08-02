from . import get_user_model
from .github import get_token, get_user_data
from .exceptions import AuthException


class VerbaBackend(object):
    """
    Django authentication backend which authenticates against the GitHub API.
    """

    def authenticate(self, code=None):
        """
        Returns a valid `VerbaUser` if the authentication is successful
        or None if the token is invalid.
        """
        try:
            token = get_token(code)
        except AuthException:
            return
        user_data = get_user_data(token)

        UserModel = get_user_model()
        return UserModel(user_data['id'], token, user_data=user_data)

    def get_user(self, pk, token, user_data={}):
        UserModel = get_user_model()
        return UserModel(pk, token, user_data=user_data)
