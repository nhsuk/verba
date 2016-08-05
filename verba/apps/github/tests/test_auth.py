import json
import responses


from github.auth import get_token
from github.exceptions import AuthValidationError

from github.tests.test_base import BaseGithubTestCase


class GetTokenTestCase(BaseGithubTestCase):
    def setUp(self):
        super(GetTokenTestCase, self).setUp()
        self.access_token_url = self.get_github_http_url('login/oauth/access_token')

    @responses.activate
    def test_success(self):
        expected_token = 'token'
        responses.add(
            responses.POST, self.access_token_url,
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
            responses.POST, self.access_token_url,
            body=json.dumps(response_body), status=200,
            content_type='application/json'
        )

        self.assertRaises(AuthValidationError, get_token, code='code')

    @responses.activate
    def test_github_returns_404(self):
        responses.add(
            responses.POST, self.access_token_url,
            status=404, content_type='application/json'
        )

        self.assertRaises(AuthValidationError, get_token, code='code')
