from django.utils.dateparse import parse_datetime

import github

from github.tests.test_base import BaseGithubTestCase


class PullDataTestCase(BaseGithubTestCase):
    def setUp(self):
        super(PullDataTestCase, self).setUp()

        self.data = {
            'body': 'some body',
            'created_at': "2016-08-05T13:15:21Z",
            'user': {
                'login': 'test-owner'
            }
        }
        self.comment = github.Comment(self.TOKEN, self.data)

    def test_basic_data(self):
        self.assertEqual(self.comment.body, self.data['body'])
        self.assertEqual(self.comment.created_at, parse_datetime(self.data['created_at']))
        self.assertEqual(self.comment.created_by, self.data['user']['login'])
