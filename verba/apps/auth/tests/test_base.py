import json
import responses

from django.test import SimpleTestCase
from django.core.urlresolvers import reverse

from verba_settings import config

from auth import SESSION_KEY


class AuthTestCase(SimpleTestCase):
    def setUp(self):
        super(AuthTestCase, self).setUp()

        # next is a 404 so that it doesn't trigger any other external call
        self.callback_url = '{}?code={}&redirect_url={}'.format(
            reverse('auth:callback'),
            'code',
            '/test-login-success/'
        )

    def get_user_data(self, **kwargs):
        user_data = {
            'login': 'github-user',
            'name': 'GitHub name',
            'email': 'example@email.com',
            'avatar_url': 'https://example.com'
        }
        user_data.update(kwargs)
        return user_data

    @responses.activate
    def login(self, token="123456789", user_data=None):
        if not user_data:
            user_data = self.get_user_data()

        responses.add(
            responses.POST, '{}/login/oauth/access_token'.format(config.GITHUB_HTTP_HOST),
            body=json.dumps({"access_token": token}), status=200,
            content_type='application/json'
        )
        responses.add(
            responses.GET, '{}/user'.format(config.GITHUB_API_HOST),
            body=json.dumps(user_data), status=200,
            content_type='application/json'
        )

        response = self.client.get(self.callback_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.client.session[SESSION_KEY], user_data['login']
        )
