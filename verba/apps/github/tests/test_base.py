import os

from verba_settings import config

from django.test import SimpleTestCase


class BaseGithubTestCase(SimpleTestCase):
    TOKEN = '123abc'

    def get_github_http_url(self, url_part):
        return '{}/{}'.format(
            config.GITHUB_HTTP_HOST,
            url_part
        )

    def get_github_api_url(self, url_part):
        return '{}/{}'.format(
            config.GITHUB_API_HOST,
            url_part
        )

    def get_github_api_repo_url(self, url_part):
        return '{}/repos/{}/{}'.format(
            config.GITHUB_API_HOST,
            config.REPO,
            url_part
        )

    def get_github_http_repo_url(self, url_part):
        return '{}/repos/{}/{}'.format(
            config.GITHUB_HTTP_HOST,
            config.REPO,
            url_part
        )

    def get_fixture(self, fixture):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(current_dir, 'fixtures', fixture)
        with open(path) as data:
            return data.read()
