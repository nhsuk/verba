import datetime
from unittest import mock

from verba_settings import config

from django.test import SimpleTestCase

from revision.models import RevisionManager, Revision
from revision.utils import generate_verba_branch_name
from revision.constants import REVISION_LOG_FILE_COMMIT_MSG, REVISION_BODY_MSG


@mock.patch('revision.models.Repo')
class RevisionManagerTestCase(SimpleTestCase):
    def test_get_all(self, MockedRepo):  # noqa
        pulls = [
            mock.MagicMock(issue_nr=1, head_ref=generate_verba_branch_name('test1', 'test-owner')),
            mock.MagicMock(issue_nr=3, head_ref='another-name'),
            mock.MagicMock(issue_nr=2, head_ref=generate_verba_branch_name('test2', 'test-owner')),
        ]
        MockedRepo().get_pulls.return_value = pulls

        manager = RevisionManager(token='123456')
        revisions = manager.get_all()

        self.assertEqual(len(revisions), 2)
        self.assertEqual(
            sorted([rev.id for rev in revisions]),
            [pulls[0].issue_nr, pulls[2].issue_nr]
        )

    @mock.patch('revision.models.timezone')
    def test_create(self, mocked_timezone, MockedRepo):  # noqa
        title = 'test-title'
        creator = 'test-owner'
        manager = RevisionManager(token='123456')
        mocked_timezone.now.return_value = datetime.datetime(day=1, month=1, year=2016)

        mocked_repo = MockedRepo()

        def mocked_create_pull(**kwargs):
            head = kwargs['head']
            return mock.MagicMock(head_ref=head)
        mocked_repo.create_pull.side_effect = mocked_create_pull

        # main call
        rev = manager.create(title, creator)

        # check create_branch called
        mocked_create_branch = mocked_repo.create_branch
        mocked_create_branch.assert_called_with(
            new_branch=rev._pull.head_ref,
            from_branch=config.BRANCHES.BASE
        )

        # checked new file revision log created
        mocked_branch = mocked_create_branch()
        mocked_branch.create_new_file.assert_called_with(
            content='',
            message=REVISION_LOG_FILE_COMMIT_MSG,
            path='{}2016.01.01_00.00_{}'.format(
                config.PATHS.REVISIONS_LOG_FOLDER,
                rev._pull.head_ref
            )
        )

        # check PR created
        mocked_repo.create_pull.assert_called_with(
            title=title,
            body=REVISION_BODY_MSG.format(title=title),
            base=config.BRANCHES.BASE,
            head=rev._pull.head_ref
        )

        # check status and assignee
        self.assertEqual(rev.statuses, [config.LABELS.DRAFT])
        self.assertEqual(rev.assignees, ['test-owner'])


class RevisionTestCase(SimpleTestCase):
    def setUp(self):
        super(RevisionTestCase, self).setUp()
        self.revision = Revision(
            pull=mock.MagicMock(
                issue_nr=1,
                head_ref=generate_verba_branch_name('test title', 'test-owner'),
                title='rev title',
                labels=config.LABELS.ALLOWED + ['another-label'],
                assignees=config.ASSIGNEES.ALLOWED + ['another-user']
            )
        )

    def test_id(self):
        self.assertEqual(
            self.revision.id, 1
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

    def test_creator(self):
        self.assertEqual(
            self.revision.creator,
            'test-owner'
        )

    def test_move_to_draft(self):
        self.revision.move_to_draft()

        self.assertEqual(
            self.revision.statuses,
            [config.LABELS.DRAFT]
        )
        self.assertEqual(
            sorted(self.revision._pull.labels),
            sorted(['another-label', config.LABELS.DRAFT])
        )

        self.assertEqual(
            self.revision.assignees,
            ['test-owner']
        )
        self.assertEqual(
            sorted(self.revision._pull.assignees),
            sorted(['another-user', 'test-owner'])
        )
