from django.test import SimpleTestCase

from verba_settings import config

from revision.utils import is_verba_branch, generate_verba_branch_name, get_verba_branch_name_info
from revision.constants import BRANCH_PARTS_SEPARATOR


class IsVerbaBranchTestCase(SimpleTestCase):
    def test_true(self):
        parts = [
            config.BRANCHES.NAMESPACE,
            'title',
            'some-creator',
            'random-string'
        ]

        self.assertTrue(
            is_verba_branch(BRANCH_PARTS_SEPARATOR.join(parts))
        )

    def test_false(self):
        parts = [
            config.BRANCHES.NAMESPACE,
            'title',
            'some-creator',
            'random-string'
        ]

        self.assertFalse(
            is_verba_branch(BRANCH_PARTS_SEPARATOR.join(parts[1:]))
        )
        self.assertFalse(
            is_verba_branch(BRANCH_PARTS_SEPARATOR.join(parts[:-1]))
        )
        self.assertFalse(
            is_verba_branch('%'.join(parts))
        )


class GenerateVerbaBranchNameTestCase(SimpleTestCase):
    def test_generate(self):
        title = 'test title'
        creator = 'test-owner'

        branch_name = generate_verba_branch_name(title, creator)

        parts = branch_name.split(BRANCH_PARTS_SEPARATOR)
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], config.BRANCHES.NAMESPACE)
        self.assertEqual(parts[1], 'test-title')
        self.assertEqual(parts[2], 'test-owner')


class GetVerbaBranchNameInfo(SimpleTestCase):
    def test_valid(self):
        parts = [
            config.BRANCHES.NAMESPACE,
            'test-title',
            'some-creator',
            'random-string'
        ]
        branch_name = BRANCH_PARTS_SEPARATOR.join(parts)

        namespace, title, creator, random_string = get_verba_branch_name_info(branch_name)
        self.assertEqual(namespace, parts[0])
        self.assertEqual(title, parts[1])
        self.assertEqual(creator, parts[2])
        self.assertEqual(random_string, parts[3])

    def test_invalid(self):
        parts = [
            config.BRANCHES.NAMESPACE,
            'test-title',
            'some-creator',
            'random-string'
        ]

        self.assertEqual(
            get_verba_branch_name_info('%'.join(parts)),
            (None, None, None, None)
        )

        self.assertEqual(
            get_verba_branch_name_info(BRANCH_PARTS_SEPARATOR.join(parts[1:])),
            (None, None, None, None)
        )
        self.assertEqual(
            get_verba_branch_name_info(BRANCH_PARTS_SEPARATOR.join(parts[:-1])),
            (None, None, None, None)
        )

        self.assertEqual(
            get_verba_branch_name_info('random-string'),
            (None, None, None, None)
        )
