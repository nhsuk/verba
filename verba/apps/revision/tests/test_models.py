from unittest import mock

from verba_settings import config

from django.test import SimpleTestCase

from revision.models import is_verba_branch, RevisionManager, Revision


class IsVerbaBranchTestCase(SimpleTestCase):
    def test_true(self):
        self.assertTrue(
            is_verba_branch(config.BRANCHES.NAMESPACE)
        )
        self.assertTrue(
            is_verba_branch('{}test'.format(config.BRANCHES.NAMESPACE))
        )

    def test_false(self):
        self.assertFalse(
            is_verba_branch(config.BRANCHES.NAMESPACE.upper())
        )
        self.assertFalse(
            is_verba_branch('some-test')
        )


class RevisionManagerTestCase(SimpleTestCase):
    @mock.patch('revision.models.Repo')
    def test_get_all(self, MockedRepo):  # noqa
        pulls = [
            mock.MagicMock(head_ref='{}test1'.format(config.BRANCHES.NAMESPACE)),
            mock.MagicMock(head_ref='another-name'),
            mock.MagicMock(head_ref='{}test2'.format(config.BRANCHES.NAMESPACE)),
        ]
        MockedRepo().get_pulls.return_value = pulls

        manager = RevisionManager(token='123456')
        revisions = manager.get_all()

        self.assertEqual(len(revisions), 2)
        self.assertEqual(
            sorted([rev.id for rev in revisions]),
            [
                '{}test1'.format(config.BRANCHES.NAMESPACE),
                '{}test2'.format(config.BRANCHES.NAMESPACE)
            ]
        )


class RevisionTestCase(SimpleTestCase):
    def setUp(self):
        super(RevisionTestCase, self).setUp()
        self.revision = Revision(
            pull=mock.MagicMock(
                title='rev title',
                labels=config.LABELS.ALLOWED + ['another-label'],
                assignees=config.ASSIGNEES.ALLOWED + ['another-user']
            ),
            revision_id='some-id'
        )

    def test_title(self):
        self.assertEqual(
            self.revision.title, 'rev title'
        )

    def test_statuses(self):
        self.assertEqual(
            sorted(self.revision.statuses),
            sorted(config.LABELS.ALLOWED)
        )

    def test_assignees(self):
        self.assertEqual(
            sorted(self.revision.assignees),
            sorted(config.ASSIGNEES.ALLOWED)
        )
