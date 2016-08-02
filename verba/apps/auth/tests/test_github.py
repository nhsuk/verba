import json
import responses

from django.test import SimpleTestCase

from auth.github import get_token, get_user_data
from auth.exceptions import AuthValidationError


class GetTokenTestCase(SimpleTestCase):
    @responses.activate
    def test_success(self):
        expected_token = 'token'
        responses.add(
            responses.POST, 'https://github.com/login/oauth/access_token',
            body=json.dumps({"access_token": expected_token}), status=200,
            content_type='application/json'
        )

        token = get_token(code='code')
        self.assertEqual(token, expected_token)

    @responses.activate
    def test_invalid_code(self):
        response_body = {
            'error': 'bad_verification_code',
            'error_uri': 'https://developer.github.com/v3/oauth/#bad-verification-code',
            'error_description': 'The code passed is incorrect or expired.'
        }
        responses.add(
            responses.POST, 'https://github.com/login/oauth/access_token',
            body=json.dumps(response_body), status=200,
            content_type='application/json'
        )

        self.assertRaises(AuthValidationError, get_token, code='code')

    @responses.activate
    def test_github_returns_404(self):
        responses.add(
            responses.POST, 'https://github.com/login/oauth/access_token',
            status=404,
            content_type='application/json'
        )

        self.assertRaises(AuthValidationError, get_token, code='code')


class GetUserDataTestCase(SimpleTestCase):
    @responses.activate
    def test_success(self):
        expected_user_data = {'id': 1}
        responses.add(
            responses.GET, 'https://api.github.com/user',
            body=json.dumps(expected_user_data), status=200,
            content_type='application/json'
        )

        user_data = get_user_data(token='token')
        self.assertDictEqual(user_data, expected_user_data)

    @responses.activate
    def test_invalid_token(self):
        response_body = {
            'message': 'Bad credentials',
            'documentation_url': 'https://developer.github.com/v3'
        }

        responses.add(
            responses.GET, 'https://api.github.com/user',
            body=json.dumps(response_body), status=401,
            content_type='application/json'
        )

        self.assertRaises(AuthValidationError, get_user_data, token='invalid token')
