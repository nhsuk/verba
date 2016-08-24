from unittest import mock

from django.test.testcases import SimpleTestCase

from revision.forms import NewRevisionForm, ContentForm
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


class ContentFormTestCase(SimpleTestCase):
    def setUp(self):
        self.content_items = {
            'right-content': 'some value for right content',
            'sub-title': 'some value for sub title',
            'title': 'some value for title'
        }
        self.revision_file = mock.MagicMock()
        self.revision_file.get_content_items.return_value = self.content_items

    def test_fields(self):
        form = ContentForm(revision_file=self.revision_file)

        self.assertEqual(
            list(form.fields.keys()),
            ['title', 'right-content', 'sub-title']
        )

        self.assertEqual(form.fields['title'].initial, self.content_items['title'])
        self.assertEqual(form.fields['sub-title'].initial, self.content_items['sub-title'])
        self.assertEqual(form.fields['right-content'].initial, self.content_items['right-content'])

    def test_empty_field(self):
        form = ContentForm(
            revision_file=self.revision_file,
            data={
                'title': '',
                'sub-title': 'some other value'
            }
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['title'], ['This field is required.'])

    def test_valid(self):
        form = ContentForm(
            revision_file=self.revision_file,
            data={
                'title': 'new title',
                'sub-title': 'some other value',
                'right-content': 'some new right content'
            }
        )

        self.assertTrue(form.is_valid())

        form.save()
        self.revision_file.save_content_items.assert_called_with(form.cleaned_data)
