import json
import responses

import github
from github.exceptions import InvalidResponseException

from github.tests.test_base import BaseGithubTestCase


class BaseUserTestCase(BaseGithubTestCase):
    def setUp(self):
        super(BaseUserTestCase, self).setUp()

        self.data = {
            'login': 'github-user',
            'name': 'GitHub name',
            'email': 'example@email.com',
            'avatar_url': 'https://example.com'
        }
        self.user = github.User(self.TOKEN, self.data)


class UserDataTestCase(BaseUserTestCase):
    def test_basic_data(self):
        self.assertEqual(self.user.username, self.data['login'])
        self.assertEqual(self.user.name, self.data['name'])
        self.assertEqual(self.user.email, self.data['email'])
        self.assertEqual(self.user.avatar_url, self.data['avatar_url'])


class GetLoggedInUserTestCase(BaseUserTestCase):
    @responses.activate
    def test_success(self):
        responses.add(
            responses.GET, self.get_github_api_url('user'),
            body=json.dumps(self.data), status=200,
            content_type='application/json'
        )

        github_user = github.User.get_logged_in(token=self.TOKEN)
        self.assertEqual(github_user.username, self.data['login'])

    @responses.activate
    def test_invalid_token(self):
        response_body = {
            'message': 'Bad credentials',
            'documentation_url': 'https://developer.github.com/v3'
        }

        responses.add(
            responses.GET, self.get_github_api_url('user'),
            body=json.dumps(response_body), status=401,
            content_type='application/json'
        )

        self.assertRaises(InvalidResponseException, github.User.get_logged_in, token='invalid token')
