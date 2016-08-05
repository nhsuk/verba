from github import User as GitHubUser
from github.auth import get_token
from github.exceptions import AuthValidationError

from . import get_user_model


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
        except AuthValidationError:
            return
        github_user = GitHubUser.get_logged_in(token)

        UserModel = get_user_model()
        return UserModel(
            pk=github_user.username,
            token=token,
            user_data={
                'name': github_user.name,
                'email': github_user.email,
                'avatar_url': github_user.avatar_url
            }
        )

    def get_user(self, pk, token, user_data={}):
        UserModel = get_user_model()
        return UserModel(pk, token, user_data=user_data)
