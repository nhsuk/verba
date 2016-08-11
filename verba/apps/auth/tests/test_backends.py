from unittest import mock

from github.exceptions import AuthValidationError
from github import User as GitHubUser

from auth.backends import VerbaBackend

from .test_base import AuthTestCase


@mock.patch('auth.backends.get_token')
class VerbaBackendTestCase(AuthTestCase):
    def test_authenticate_fails(self, mocked_get_token):
        mocked_get_token.side_effect = AuthValidationError('', '')

        backend = VerbaBackend()
        self.assertEqual(backend.authenticate(code='code'), None)

    @mock.patch('auth.backends.GitHubUser')
    def test_success(self, mocked_github_ser, mocked_get_token):
        user_data = self.get_user_data()
        mocked_github_ser.get_logged_in.return_value = GitHubUser(
            token='token', data=user_data
        )

        backend = VerbaBackend()
        user = backend.authenticate(code='code')
        self.assertEqual(user.pk, user_data['login'])
        self.assertEqual(user.user_data['name'], user_data['name'])
