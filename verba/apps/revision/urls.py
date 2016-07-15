from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.RevisionList.as_view(), name='list'),
    url(
        r'^(?P<revision_name>[\w-]+)/$',
        views.RevisionDetail.as_view(),
        name='detail'
    ),
    url(
        r'^(?P<revision_name>[\w-]+)/(?P<file_path>.+)$',
        views.RevisionFileDetail.as_view(),
        name='file-detail'
    ),
]
