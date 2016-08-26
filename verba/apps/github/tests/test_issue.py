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
            ],
            'comments_url': self.get_github_api_repo_url('issues/1/comments')
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


class IssueCommentsTestCase(BaseIssueTestCase):
    @responses.activate
    def test_comments(self):
        responses.add(
            responses.GET, self.data['comments_url'],
            body=self.get_fixture('comments.json'), status=200,
            content_type='application/json'
        )

        comments = self.issue.comments
        self.assertEqual(len(comments), 2)
        self.assertEqual(
            [comment.body for comment in comments],
            ['test comment 1', 'test comment 2']
        )

    @responses.activate
    def test_add_valid_comment(self):
        responses.add(
            responses.POST, self.data['comments_url'],
            body=self.get_fixture('comment.json'), status=200,
            content_type='application/json'
        )

        self.issue.add_comment('test comment')
        self.assertEqual(len(responses.calls), 1)
        request, response = responses.calls[0]
        self.assertTrue(response.ok)

    @responses.activate
    def test_add_empty_comment(self):
        responses.add(
            responses.POST, self.data['comments_url'],
            body=json.dumps({
                'message': 'Validation Failed',
                'documentation_url': 'https://developer.github.com/v3/issues/comments/#create-a-comment',
                'errors': [{
                    'resource': 'IssueComment',
                    'message': 'body cannot be blank',
                    'field': 'body',
                    'code': 'custom'
                }]
            }),
            status=422, content_type='application/json'
        )

        self.assertRaises(
            InvalidResponseException,
            self.issue.add_comment, ''
        )
