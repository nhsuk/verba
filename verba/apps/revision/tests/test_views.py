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
