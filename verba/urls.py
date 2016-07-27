from django.views.generic.base import RedirectView
from django.conf.urls import url, include


urlpatterns = [
    url(r'^$', RedirectView.as_view(url='/revision/', permanent=False), name='index'),
    url(r'^revision/', include('revision.urls', namespace='revision')),
    url(r'^auth/', include('auth.urls', namespace='auth')),
]
