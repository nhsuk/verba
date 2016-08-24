from unittest import mock

from django.core.urlresolvers import reverse

from auth.tests.test_base import AuthTestCase

from revision.exceptions import RevisionNotFoundException


@mock.patch('revision.views.RevisionManager')
class RevisionListTestCase(AuthTestCase):
    def setUp(self):
        super(RevisionListTestCase, self).setUp()
        self.url = reverse('revision:list')

    def test_redirects_to_login(self, MockedRevisionManager):  # noqa
        self._test_redirects_to_login(self.url)

    def test_get(self, MockedRevisionManager):  # noqa
        revisions = [
            mock.MagicMock(), mock.MagicMock()
        ]
        MockedRevisionManager().get_all.return_value = revisions

        self.login()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.context['revisions'], revisions)


@mock.patch('revision.views.RevisionManager')
class NewRevisionTestCase(AuthTestCase):
    def setUp(self):
        super(NewRevisionTestCase, self).setUp()
        self.url = reverse('revision:new')

    def test_redirects_to_login(self, MockedRevisionManager):  # noqa
        self._test_redirects_to_login(self.url)

    def test_invalid_title(self, MockedRevisionManager):  # noqa
        self.login()

        response = self.client.post(self.url, data={
            'title': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_success(self, MockedRevisionManager):  # noqa
        mocked_manager = MockedRevisionManager()
        mocked_manager.create.return_value = mock.MagicMock(id=1)

        self.login()

        title = 'test title'
        response = self.client.post(self.url, data={'title': title})
        self.assertEqual(response.status_code, 302)

        mocked_manager.create.assert_called_with(
            title, self.get_user_data()['login']
        )


class BaseRevisionDetailTestCase(AuthTestCase):
    def get_mocked_revision(self):
        return mock.MagicMock(
            assignees=[
                self.get_user_data()['login']
            ]
        )

    def _test_non_assignees_not_allowed(self, MockedRevisionManager):  # noqa
        revision = mock.MagicMock(
            assignees=['some-user']
        )
        MockedRevisionManager().get.return_value = revision

        self.login()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


@mock.patch('revision.views.RevisionManager')
class EditorTestCase(BaseRevisionDetailTestCase):
    def setUp(self):
        super(EditorTestCase, self).setUp()
        self.url = reverse('revision:editor', kwargs={'revision_id': 1})

    def test_redirects_to_login(self, MockedRevisionManager):  # noqa
        self._test_redirects_to_login(self.url)

    def test_non_assignees_not_allowed(self, MockedRevisionManager):  # noqa
        self._test_non_assignees_not_allowed(MockedRevisionManager)

    def test_get_found(self, MockedRevisionManager):  # noqa
        revision = self.get_mocked_revision()
        rev_files = [
            mock.MagicMock(), mock.MagicMock()
        ]
        revision.get_files.return_value = rev_files
        MockedRevisionManager().get.return_value = revision

        self.login()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['revision'], revision)
        self.assertEqual(revision.get_files(), rev_files)

    def test_get_not_found(self, MockedRevisionManager):  # noqa
        MockedRevisionManager().get.side_effect = RevisionNotFoundException()

        self.login()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


@mock.patch('revision.views.RevisionManager')
class EditFileTestCase(BaseRevisionDetailTestCase):
    def setUp(self):
        super(EditFileTestCase, self).setUp()
        self.url = reverse('revision:edit-file', kwargs={'revision_id': 1, 'file_path': 'somet-path/some-file/'})

        self.revision = self.get_mocked_revision()
        self.revision_file = mock.MagicMock()
        self.revision_file.get_content_items.return_value = {
            'title': 'some title',
            'content': 'some content'
        }
        self.revision.get_file.return_value = self.revision_file

    def test_redirects_to_login(self, MockedRevisionManager):  # noqa
        self._test_redirects_to_login(self.url)

    def test_non_assignees_not_allowed(self, MockedRevisionManager):  # noqa
        self._test_non_assignees_not_allowed(MockedRevisionManager)

    def test_invalid_title(self, MockedRevisionManager):  # noqa
        MockedRevisionManager().get.return_value = self.revision

        self.login()

        response = self.client.post(self.url, data={
            'title': '',
            'content': 'some content'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_success(self, MockedRevisionManager):  # noqa
        MockedRevisionManager().get.return_value = self.revision

        self.login()

        data = {
            'title': 'new title',
            'content': 'new content'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.revision_file.save_content_items.assert_called_with(data)
