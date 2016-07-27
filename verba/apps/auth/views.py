from django.conf import settings
from django.views.generic.base import View
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.http import is_safe_url
from django.core.urlresolvers import reverse
from django.shortcuts import resolve_url
from django.utils.six.moves.urllib.parse import urlparse, urlunparse
from django.http import QueryDict

from . import login as auth_login, logout as auth_logout
from .forms import AuthenticationForm
from .github import get_login_url


class LoginView(View):
    """
    Redirects to the GitHub authenticate URL.
    """
    def get(self, request, *args, **kwargs):
        # check if next page is in URL
        redirect_to = request.POST.get(
            REDIRECT_FIELD_NAME,
            request.GET.get(REDIRECT_FIELD_NAME, '')
        )

        # Security check -- don't allow redirection to a different host.
        if redirect_to and not is_safe_url(url=redirect_to, host=request.get_host()):
            redirect_to = None

        # if next, construct callback_url else leave it None and the default one will be used
        callback_url = None
        if redirect_to:
            callback_url = '{}?redirect_url={}'.format(
                request.build_absolute_uri(reverse('auth:callback')),
                redirect_to
            )

        url = get_login_url(callback_url=callback_url)
        return HttpResponseRedirect(url)


class CallbackView(View):
    """
    Called by GitHub when authenticating.
    """
    def get(self, request, *args, **kwargs):
        redirect_url = request.GET.get('redirect_url', '/')

        form = AuthenticationForm(request, request.GET)

        if form.is_valid():
            auth_login(request, form.get_user())
            return HttpResponseRedirect(redirect_url)

        return HttpResponse('Unauthorized', status=401)


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        auth_logout(request)

        next_page = None
        if (REDIRECT_FIELD_NAME in request.POST or
                REDIRECT_FIELD_NAME in request.GET):
            next_page = request.POST.get(
                REDIRECT_FIELD_NAME, request.GET.get(REDIRECT_FIELD_NAME)
            )
            # Security check -- don't allow redirection to a different host.
            if not is_safe_url(url=next_page, host=request.get_host()):
                next_page = request.path

        if next_page:
            # Redirect to this page until the session has been cleared.
            return HttpResponseRedirect(next_page)

        return HttpResponseRedirect('/')


def redirect_to_login(next, login_url=None,
                      redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Redirects the user to the login page, passing the given 'next' page
    """
    resolved_url = resolve_url(login_url or settings.LOGIN_URL)

    login_url_parts = list(urlparse(resolved_url))
    if redirect_field_name:
        querystring = QueryDict(login_url_parts[4], mutable=True)
        querystring[redirect_field_name] = next
        login_url_parts[4] = querystring.urlencode(safe='/')

    return HttpResponseRedirect(urlunparse(login_url_parts))
