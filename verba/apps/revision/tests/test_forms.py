from unittest import mock

from django.test.testcases import SimpleTestCase

from revision.forms import NewRevisionForm
from revision.constants import BRANCH_PARTS_SEPARATOR


class NewRevisionFormTestCase(SimpleTestCase):
    def setUp(self):
        super(NewRevisionFormTestCase, self).setUp()
        self.revision_manager = mock.MagicMock()

    def test_valid(self):
        data = {'title': 'test title'}
        creator = 'test-owner'

        form = NewRevisionForm(
            revision_manager=self.revision_manager,
            data=data
        )

        self.assertTrue(form.is_valid())

        form.save(creator)
        self.revision_manager.create.assert_called_with(data['title'], creator)

    def test_empty_title(self):
        form = NewRevisionForm(
            revision_manager=self.revision_manager,
            data={'title': ''}
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['title'], ['This field is required.'])

    def test_invalid_char_in_title(self):
        form = NewRevisionForm(
            revision_manager=self.revision_manager,
            data={
                'title': 'test {} title'.format(BRANCH_PARTS_SEPARATOR)
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['title'],
            ["Char '{}' not allowed".format(BRANCH_PARTS_SEPARATOR)]
        )
