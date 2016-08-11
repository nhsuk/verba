import json
import responses

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.urlresolvers import reverse

from verba_settings import config

from auth import SESSION_KEY, BACKEND_SESSION_KEY, \
    AUTH_TOKEN_SESSION_KEY, USER_DATA_SESSION_KEY

from .test_base import AuthTestCase


class LoginViewTestCase(AuthTestCase):
    def test_success(self):
        token = "123456789"
        user_data = self.get_user_data()
        self.login(token, user_data=user_data)

        self.assertEqual(
            self.client.session[SESSION_KEY], user_data['login']
        )
        self.assertEqual(
            self.client.session[BACKEND_SESSION_KEY],
            settings.AUTHENTICATION_BACKENDS[0]
        )
        self.assertEqual(
            self.client.session[AUTH_TOKEN_SESSION_KEY], token
        )
        self.assertEqual(
            self.client.session[USER_DATA_SESSION_KEY]['name'], user_data['name']
        )

    @responses.activate
    def test_invalid_auth_code(self):
        response_body = {
            'error': 'bad_verification_code',
            'error_uri': 'https://developer.github.com/v3/oauth/#bad-verification-code',
            'error_description': 'The code passed is incorrect or expired.'
        }
        responses.add(
            responses.POST, '{}/login/oauth/access_token'.format(config.GITHUB_HTTP_HOST),
            body=json.dumps(response_body), status=200,
            content_type='application/json'
        )
        response = self.client.get(self.callback_url)
        self.assertEqual(response.status_code, 401)


class LogoutViewTestCase(AuthTestCase):
    def setUp(self):
        super(LogoutViewTestCase, self).setUp()

        # next is a 404 so that it doesn't trigger any other external call
        self.logout_url = '{}?{}={}'.format(
            reverse('auth:logout'),
            REDIRECT_FIELD_NAME, '/test-logout-success/'
        )

    def test_logout_clears_session(self):
        self.login()

        self.client.get(self.logout_url, follow=True)

        # nothing in the session
        self.assertEqual(len(self.client.session.items()), 0)
