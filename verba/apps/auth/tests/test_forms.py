from unittest import mock

from django.test.testcases import SimpleTestCase
from django.utils.encoding import force_text

from auth.forms import AuthenticationForm


@mock.patch('auth.forms.authenticate')
class AuthenticationFormTestCase(SimpleTestCase):
    def setUp(self):
        super(AuthenticationFormTestCase, self).setUp()
        self.data = {
            'code': '123456789'
        }

    def test_invalid_code(self, mocked_authenticate):
        """
        Invalid code supplied.
        """
        mocked_authenticate.return_value = None

        form = AuthenticationForm(data=self.data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.non_field_errors(),
            [force_text(form.error_messages['invalid_login'])]
        )

        mocked_authenticate.assert_called_with(**self.data)

    def test_success(self, mocked_authenticate):
        user = mock.MagicMock()
        mocked_authenticate.return_value = user

        form = AuthenticationForm(data=self.data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.non_field_errors(), [])
        self.assertTrue(form.get_user(), user)

        mocked_authenticate.assert_called_with(**self.data)
