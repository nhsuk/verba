import json
import responses

import github
from github.exceptions import InvalidResponseException

from github.tests.test_base import BaseGithubTestCase


class BaseIssueTestCase(BaseGithubTestCase):
    def setUp(self):
        super(BaseIssueTestCase, self).setUp()

        self.data = {
            'url': self.get_github_api_repo_url('issues/1'),
            'labels': [
                {'name': 'label1'},
                {'name': 'label2'}
            ],
            'assignees': [
                {'login': 'user1'},
                {'login': 'user2'}
            ]
        }
        self.issue = github.Issue(self.TOKEN, self.data)


class IssueLabelsTestCase(BaseIssueTestCase):
    def test_get(self):
        self.assertListEqual(
            self.issue.labels, ['label1', 'label2']
        )

    @responses.activate
    def test_change(self):
        responses.add(
            responses.PATCH, self.data['url'],
            body=self.get_fixture('issue.json'), status=200,
            content_type='application/json'
        )

        new_labels = ['do not merge', 'for review']
        self.issue.labels = new_labels
        self.assertDictEqual(
            json.loads(responses.calls[0].request.body), {
                'labels': new_labels
            }
        )

        self.assertListEqual(
            self.issue.labels, new_labels
        )

    @responses.activate
    def test_change_invalid(self):
        responses.add(
            responses.PATCH, self.data['url'],
            body=json.dumps({
                "message": "Invalid request.\n\nFor 'properties/labels', {} is not an array.",
                "documentation_url": "https://developer.github.com/v3/issues/#edit-an-issue"
            }),
            status=422, content_type='application/json'
        )

        try:
            self.issue.labels = {}
        except InvalidResponseException:
            pass
        else:
            self.assertTrue(False, 'InvalidResponseException not raised')


class IssueAssigneesTestCase(BaseIssueTestCase):
    def test_get(self):
        self.assertListEqual(
            self.issue.assignees, ['user1', 'user2']
        )

    @responses.activate
    def test_change(self):
        responses.add(
            responses.PATCH, self.data['url'],
            body=self.get_fixture('issue.json'), status=200,
            content_type='application/json'
        )

        new_assignees = ['test-owner']
        self.issue.assignees = new_assignees
        self.assertDictEqual(
            json.loads(responses.calls[0].request.body), {
                'assignees': new_assignees
            }
        )

        self.assertListEqual(
            self.issue.assignees, new_assignees
        )

    @responses.activate
    def test_change_invalid_assignee(self):
        responses.add(
            responses.PATCH, self.data['url'],
            body=json.dumps({
                "documentation_url": "https://developer.github.com/v3/issues/#edit-an-issue",
                "message": "Validation Failed",
                "errors": [
                    {
                        "value": "invalid-owner",
                        "resource": "Issue",
                        "field": "assignees",
                        "code": "invalid"
                    }
                ]
            }),
            status=422, content_type='application/json'
        )

        try:
            self.issue.labels = ['invalid-owner']
        except InvalidResponseException:
            pass
        else:
            self.assertTrue(False, 'InvalidResponseException not raised')
