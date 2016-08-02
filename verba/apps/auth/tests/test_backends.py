from unittest import mock

from django.test import SimpleTestCase

from auth.backends import VerbaBackend
from auth.exceptions import AuthException


@mock.patch('auth.backends.get_token')
class VerbaBackendTestCase(SimpleTestCase):
    def test_authenticate_fails(self, mocked_get_token):
        mocked_get_token.side_effect = AuthException()

        backend = VerbaBackend()
        self.assertEqual(backend.authenticate(code='code'), None)

    @mock.patch('auth.backends.get_user_data')
    def test_success(self, mocked_get_user_data, mocked_get_token):
        token = 'token'
        user_data = {
            'id': 1
        }

        mocked_get_token.return_value = token
        mocked_get_user_data.return_value = user_data

        backend = VerbaBackend()
        user = backend.authenticate(code='code')
        self.assertEqual(user.pk, user_data['id'])
        self.assertEqual(user.token, token)
        self.assertDictEqual(user.user_data, user_data)
