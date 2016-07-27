from unittest import mock

from django.test import SimpleTestCase

from auth import login, logout, get_user, \
    SESSION_KEY, BACKEND_SESSION_KEY, USER_DATA_SESSION_KEY, HASH_SESSION_KEY, AUTH_TOKEN_SESSION_KEY
from auth.models import VerbaUser, VerbaAnonymousUser


class LoginTestCase(SimpleTestCase):
    def test_set_user_into_session(self):
        """
        If the session is empty, after calling login, it should get populated with user data.
        """
        session = self.client.session

        request = mock.MagicMock(session=session)
        user = VerbaUser(pk=1, token='user token', user_data={'username': 'verbauser'})
        user.backend = 'backend'

        login(request, user)
        self.assertEqual(request.session[SESSION_KEY], user.pk)
        self.assertEqual(request.session[BACKEND_SESSION_KEY], 'backend')
        self.assertDictEqual(request.session[USER_DATA_SESSION_KEY], user.user_data)
        self.assertNotEqual(request.session[HASH_SESSION_KEY], '')
        self.assertEqual(request.session[AUTH_TOKEN_SESSION_KEY], user.token)
        self.assertEqual(request.user, user)

    def test_flush_old_session_if_different(self):
        """
        If there's another user pk in the session, that value should get reset and overrides by the new one.
        """
        old_pk = 'old session'

        session = self.client.session
        session[SESSION_KEY] = old_pk

        request = mock.MagicMock(session=session)
        user = VerbaUser(pk=1, token='user token', user_data={'username': 'verbauser'})
        user.backend = 'backend'

        self.assertEqual(request.session[SESSION_KEY], old_pk)
        login(request, user)
        self.assertNotEqual(request.session[SESSION_KEY], old_pk)
        self.assertEqual(request.session[SESSION_KEY], user.pk)


class LogoutTestCase(SimpleTestCase):
    def test_logged_in(self):
        """
        If the user is logged in, after calling logout, the session should get flushed.
        """
        session = self.client.session
        session[SESSION_KEY] = 'some id'

        user = VerbaUser(pk=1, token='user token', user_data={'username': 'verbauser'})
        request = mock.MagicMock(session=session, user=user)
        logout(request)
        self.assertTrue(isinstance(request.user, VerbaAnonymousUser))
        self.assertFalse(SESSION_KEY in request.session)

    def test_already_logged_out(self):
        """
        If the user is already logged out, after calling logout the session should still get flushed.
        """
        session = self.client.session
        session[SESSION_KEY] = 'some id'

        user = VerbaAnonymousUser()
        request = mock.MagicMock(session=session, user=user)
        logout(request)
        self.assertTrue(isinstance(request.user, VerbaAnonymousUser))
        self.assertFalse(SESSION_KEY in request.session)


class GetUserTestCase(SimpleTestCase):
    def test_when_logged_in(self):
        """
        When the values in the session are set up properly, get_user should return the expected VerbaUser.
        """
        session = self.client.session

        expected_user = VerbaUser(pk=1, token='user token', user_data={'username': 'verbauser'})
        session[SESSION_KEY] = expected_user.pk
        session[AUTH_TOKEN_SESSION_KEY] = expected_user.token
        session[USER_DATA_SESSION_KEY] = expected_user.user_data
        session[BACKEND_SESSION_KEY] = 'auth.backends.VerbaBackend'
        session[HASH_SESSION_KEY] = expected_user.get_session_auth_hash()

        request = mock.MagicMock(session=session)

        user = get_user(request)

        self.assertEqual(user.pk, expected_user.pk)
        self.assertEqual(user.token, expected_user.token)
        self.assertDictEqual(user.user_data, expected_user.user_data)

    def test_with_invalid_hash_returns_anonymous(self):
        """
        When the values in the session are set up properly APART FROM the HASH SESSION KEY,
        get_user should return VerbaAnonymousUser
        """
        session = self.client.session

        expected_user = VerbaUser(pk=1, token='user token', user_data={'username': 'verbauser'})
        session[SESSION_KEY] = expected_user.pk
        session[AUTH_TOKEN_SESSION_KEY] = expected_user.token
        session[USER_DATA_SESSION_KEY] = expected_user.user_data
        session[BACKEND_SESSION_KEY] = 'auth.backends.VerbaBackend'
        session[HASH_SESSION_KEY] = 'some other hash'

        request = mock.MagicMock(session=session)

        user = get_user(request)
        self.assertTrue(isinstance(user, VerbaAnonymousUser))

    def test_not_logged_in_returns_anonymous(self):
        """
        When the session is empty, get_user should return VerbaAnonymousUser.
        """
        session = self.client.session
        request = mock.MagicMock(session=session)

        user = get_user(request)
        self.assertTrue(isinstance(user, VerbaAnonymousUser))
