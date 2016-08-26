import json
import datetime
from unittest import mock

from verba_settings import config

from django.test import SimpleTestCase

from github.exceptions import NotFoundException

from revision.models import RevisionManager, Revision, RevisionFile, Comment, PlainActivity
from revision.utils import generate_verba_branch_name
from revision.constants import REVISION_LOG_FILE_COMMIT_MSG, REVISION_BODY_MSG, CONTENT_FILE_MANIFEST, \
    CONTENT_FILE_INCLUSION_DIRECTIVE, FILE_CHANGED_COMMIT_MSG
from revision.exceptions import RevisionNotFoundException


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

    def test_get_found(self, MockedRepo):  # noqa
        revision_id = 1

        mocked_repo = MockedRepo()
        mocked_repo.get_pull.return_value = mock.MagicMock(
            head_ref=generate_verba_branch_name('test1', 'test-owner'),
            issue_nr=revision_id
        )

        manager = RevisionManager(token='123456')
        revision = manager.get(revision_id)

        self.assertEqual(revision.id, revision_id)

    def test_get_not_found(self, MockedRepo):  # noqa
        revision_id = 1

        mocked_repo = MockedRepo()
        mocked_repo.get_pull.side_effect = NotFoundException('')

        manager = RevisionManager(token='123456')

        self.assertRaises(
            RevisionNotFoundException,
            manager.get, revision_id
        )

    def test_get_not_verba_branch(self, MockedRepo):  # noqa
        revision_id = 1

        mocked_repo = MockedRepo()
        mocked_repo.get_pull.return_value = mock.MagicMock(
            head_ref='some-head-ref',
            issue_nr=revision_id
        )

        manager = RevisionManager(token='123456')

        self.assertRaises(
            RevisionNotFoundException,
            manager.get, revision_id
        )


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

    def test_is_in_draft_false(self):
        # no labels
        self.revision._pull.labels = []
        self.assertFalse(
            self.revision.is_in_draft()
        )

        # all labels except the DRAFT one
        labels = list(config.LABELS.ALLOWED)
        labels.remove(config.LABELS.DRAFT)
        self.revision._pull.labels = labels
        self.assertFalse(
            self.revision.is_in_draft()
        )

    def test_is_in_draft_true(self):
        # labels
        self.revision._pull.labels = config.LABELS.ALLOWED + ['another-label']
        self.assertTrue(
            self.revision.is_in_draft()
        )

    def test_is_in_2i_false(self):
        # no labels
        self.revision._pull.labels = []
        self.assertFalse(
            self.revision.is_in_2i()
        )

        # all labels except the DRAFT one
        labels = list(config.LABELS.ALLOWED)
        labels.remove(config.LABELS['2I'])
        self.revision._pull.labels = labels
        self.assertFalse(
            self.revision.is_in_2i()
        )

    def test_is_in_2i_true(self):
        # labels
        self.revision._pull.labels = config.LABELS.ALLOWED + ['another-label']
        self.assertTrue(
            self.revision.is_in_2i()
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

    def test_move_to_2i(self):
        self.revision.move_to_2i()

        self.assertEqual(
            self.revision.statuses,
            [config.LABELS['2I']]
        )
        self.assertEqual(
            sorted(self.revision._pull.labels),
            sorted(['another-label', config.LABELS['2I']])
        )

        self.assertEqual(
            self.revision.assignees,
            ['test-owner-2']
        )
        self.assertEqual(
            sorted(self.revision._pull.assignees),
            sorted(['another-user', 'test-owner-2'])
        )

    def test_move_to_ready_for_publishing(self):
        self.revision.move_to_ready_for_publishing()

        self.assertEqual(
            self.revision.statuses,
            [config.LABELS.READY_FOR_PUBLISHING]
        )
        self.assertEqual(
            sorted(self.revision._pull.labels),
            sorted(['another-label', config.LABELS.READY_FOR_PUBLISHING])
        )

        self.assertEqual(
            self.revision.assignees,
            ['test-developer']
        )
        self.assertEqual(
            sorted(self.revision._pull.assignees),
            sorted(['another-user', 'test-developer'])
        )

    def test_add_comment(self):
        self.revision.add_comment('test comment')
        self.assertEqual(self.revision._pull.add_comment.call_count, 1)

    def test_activities(self):
        self.revision._pull.created_at = datetime.datetime.now()
        self.revision._pull.comments = [
            mock.MagicMock(body='test comment1'),
            mock.MagicMock(body='test comment2'),
        ]

        activities = self.revision.activities

        # first activity is 'created'
        created_activity = activities[0]
        self.assertEqual(created_activity.description, 'created this revision')
        self.assertEqual(created_activity.created_at, self.revision._pull.created_at)
        self.assertEqual(created_activity.created_by, 'test-owner')

        # 2nd and 2rd, 'comment'
        self.assertEqual(
            [comment.body for comment in activities[1:]],
            ['test comment1', 'test comment2']
        )

    def test_get_files(self):
        git_files = [
            mock.MagicMock(path='{}some-path/test1/{}'.format(config.PATHS.CONTENT_FOLDER, CONTENT_FILE_MANIFEST)),
            mock.MagicMock(path='{}test2/manifest.txt'.format(config.PATHS.CONTENT_FOLDER)),
            mock.MagicMock(path='{}test3/{}'.format(config.PATHS.CONTENT_FOLDER, CONTENT_FILE_MANIFEST))
        ]
        self.revision._pull.branch.get_dir_files.return_value = git_files

        rev_files = self.revision.get_files()
        self.assertEqual(len(rev_files), 2)
        self.assertEqual(
            sorted([rev_file.path for rev_file in rev_files]),
            ['some-path/test1', 'test3']
        )

    def test_get_file(self):
        path = '{}some-path/test1/{}'.format(config.PATHS.CONTENT_FOLDER, CONTENT_FILE_MANIFEST)
        rev_file = self.revision.get_file(path)

        self.assertEqual(rev_file.revision, self.revision)


class RevisionFileTestCase(SimpleTestCase):
    def setUp(self):
        super(RevisionFileTestCase, self).setUp()
        mocked_file = mock.MagicMock()
        mocked_file.path = '{}some-path/test-page/{}'.format(
            config.PATHS.CONTENT_FOLDER, CONTENT_FILE_MANIFEST
        )
        self.pull = mock.MagicMock()
        self.revision_file = RevisionFile(
            _file=mocked_file, revision=mock.MagicMock(_pull=self.pull)
        )

    def test_path(self):
        self.assertEqual(
            self.revision_file.path, 'some-path/test-page'
        )

    def test_get_content_items(self):
        self.revision_file._file.content = json.dumps({
            'area1': 'some text',
            'area2': '{}some-content-file'.format(CONTENT_FILE_INCLUSION_DIRECTIVE)
        })
        self.pull.branch.get_file.return_value = mock.MagicMock(
            content='some external file content'
        )

        content_items = self.revision_file.get_content_items()
        self.pull.branch.get_file.assert_called_with(
            '{}some-path/test-page/some-content-file'.format(config.PATHS.CONTENT_FOLDER)
        )
        self.assertDictEqual(
            content_items, {
                'area1': 'some text',
                'area2': 'some external file content'
            }
        )

    def test_save_content_items(self):
        self.revision_file._file.content = json.dumps({
            'area1': 'some text',
            'area2': '{}some-content-file'.format(CONTENT_FILE_INCLUSION_DIRECTIVE)
        })
        external_git_file = mock.MagicMock(
            content='some external file content'
        )
        self.pull.branch.get_file.return_value = external_git_file

        # save
        self.revision_file.save_content_items({
            'area1': 'some new text for area1',
            'area2': 'some new text for area2'
        })

        # check that external file saved with new content
        external_git_file.change_content.assert_called_with(
            message=FILE_CHANGED_COMMIT_MSG.format(path='some-path/test-page/some-content-file'),
            new_content='some new text for area2'
        )

        # check that manifest file saved with right content
        args, kwargs = self.revision_file._file.change_content.call_args
        self.assertDictEqual(
            json.loads(args[0]), {
                'area1': 'some new text for area1',
                'area2': '{}some-content-file'.format(CONTENT_FILE_INCLUSION_DIRECTIVE)
            }
        )
        self.assertEqual(
            kwargs['message'],
            FILE_CHANGED_COMMIT_MSG.format(path='some-path/test-page'),
        )


class CommentTestCase(SimpleTestCase):
    def test_data(self):
        git_comment = mock.MagicMock(
            body='comment body',
            created_at=datetime.datetime.now(),
            created_by='test-owner'
        )
        comment = Comment(git_comment)
        self.assertEqual(comment.body, git_comment.body)
        self.assertEqual(comment.created_at, git_comment.created_at)
        self.assertEqual(comment.created_by, git_comment.created_by)
        self.assertEqual(comment.kind, 'comment')
        self.assertEqual(comment.description, 'wrote')


class PlainActivityTestCase(SimpleTestCase):
    def test_data(self):
        data = {
            'description': 'test description',
            'created_at': datetime.datetime.now(),
            'created_by': 'test-owner'
        }
        activity = PlainActivity(**data)
        self.assertEqual(activity.description, data['description'])
        self.assertEqual(activity.created_at, data['created_at'])
        self.assertEqual(activity.created_by, data['created_by'])
        self.assertEqual(activity.kind, 'plain')
