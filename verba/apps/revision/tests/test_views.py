from unittest import mock

from django.core.urlresolvers import reverse

from auth.tests.test_base import AuthTestCase


class RevisionListTestCase(AuthTestCase):
    def setUp(self):
        super(RevisionListTestCase, self).setUp()
        self.url = reverse('revision:list')

    def test_redirects_to_login(self):
        self._test_redirects_to_login(self.url)

    @mock.patch('revision.views.RevisionManager')
    def test_get(self, MockedRevisionManager):  # noqa
        revisions = [
            mock.MagicMock(), mock.MagicMock()
        ]
        MockedRevisionManager().get_all.return_value = revisions

        self.login()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.context['revisions'], revisions)


class NewRevisionTestCase(AuthTestCase):
    def setUp(self):
        super(NewRevisionTestCase, self).setUp()
        self.url = reverse('revision:new')

    def test_redirects_to_login(self):
        self._test_redirects_to_login(self.url)

    @mock.patch('revision.views.RevisionManager')
    def test_invalid_title(self, MockedRevisionManager):  # noqa
        self.login()

        response = self.client.post(self.url, data={
            'title': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    @mock.patch('revision.views.RevisionManager')
    def test_success(self, MockedRevisionManager):  # noqa
        self.login()

        title = 'test title'
        response = self.client.post(self.url, data={'title': title})
        self.assertEqual(response.status_code, 302)

        MockedRevisionManager().create_assert_called_with(
            title, self.get_user_data()['login']
        )
