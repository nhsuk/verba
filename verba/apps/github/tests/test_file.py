import json
import responses

import github
from github.exceptions import InvalidResponseException

from github.tests.test_base import BaseGithubTestCase


class BaseFileTestCase(BaseGithubTestCase):
    def setUp(self):
        super(BaseFileTestCase, self).setUp()
        self.file_name = 'index.md'
        self.path = 'pages/{}'.format(self.file_name)
        self.branch_name = 'new-branch'

        self.file_content_github_url = self.get_github_api_repo_url('contents/{}'.format(self.path))
        self.file = github.File(
            self.TOKEN, self.path, self.branch_name
        )


class FileDataTestCase(BaseFileTestCase):
    def test_name(self):
        setattr(self.file, '_cached_data', {
            'name': self.file_name
        })
        self.assertEqual(self.file.name, self.file_name)

    @responses.activate
    def test_get_data_if_not_fetched(self):
        responses.add(
            responses.GET, self.file_content_github_url,
            body=self.get_fixture('file_contents.json'),
            status=200, content_type='application/json'
        )

        self.assertEqual(self.file.name, self.file_name)
        self.assertEqual(self.file.name, self.file_name)  # intentional
        self.assertEqual(len(responses.calls), 1)  # should be 1 not 2


class CreateFileTestCase(BaseFileTestCase):
    @responses.activate
    def test_success(self):
        content = 'some content'
        responses.add(
            responses.PUT, self.file_content_github_url,
            body=self.get_fixture('new_file.json'),
            status=201, content_type='application/json'
        )

        git_file = github.File.create(
            self.TOKEN, path=self.path, branch_name=self.branch_name,
            content=content, message='some message'
        )
        self.assertEqual(git_file.name, self.file_name)
        self.assertTrue(hasattr(git_file, '_cached_data'))
        self.assertEqual(git_file.content, content)

    @responses.activate
    def test_invalid_path(self):
        responses.add(
            responses.PUT, self.file_content_github_url,
            body=json.dumps({
                "message": "Invalid request.\n\n\"sha\" wasn't supplied.",
                "documentation_url": "https://developer.github.com/v3/repos/contents/"
            }),
            status=422, content_type='application/json'
        )

        self.assertRaises(
            InvalidResponseException,
            github.File.create,
            self.TOKEN, path='pages/index.md', branch_name=self.branch_name,
            content='some content', message='some message'
        )

    @responses.activate
    def test_invalid_branch(self):
        responses.add(
            responses.PUT, self.file_content_github_url,
            body=json.dumps({
                "documentation_url": "https://developer.github.com/v3/repos/contents/",
                "message": "Branch invalid-branch not found"
            }),
            status=422, content_type='application/json'
        )

        self.assertRaises(
            InvalidResponseException,
            github.File.create,
            self.TOKEN, path=self.path, branch_name='invalid-branch',
            content='some content', message='some message'
        )


class ContentFileTestCase(BaseFileTestCase):
    def test_get(self):
        setattr(self.file, '_cached_data', {
            'content': 'SW5kZXgKLS0tLS0KdGhpcyBpcyBhIHRlc3QK\n'
        })
        self.assertEqual(self.file.content, "Index\n-----\nthis is a test\n")

    @responses.activate
    def test_change_success(self):
        # setting content just to check that it gets overridden
        setattr(self.file, '_cached_data', {
            'content': 'old content',
            'sha': 'abcdf'
        })
        responses.add(
            responses.PUT, self.file_content_github_url,
            body=self.get_fixture('file_contents.json'),
            status=200, content_type='application/json'
        )

        self.file.change_content(
            new_content='some content',
            message='new message'
        )
        self.assertEqual(self.file.content, "Index\n-----\nthis is a test\n")
