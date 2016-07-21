from django.conf.urls import url

from . import views


urlpatterns = [
    url(
        r'^$',
        views.RevisionList.as_view(),
        name='list'
    ),
    url(
        r'^new/$',
        views.NewRevision.as_view(),
        name='new'
    ),
    url(
        r'^detail/(?P<revision_id>[\w-]+)/$',
        views.RevisionDetail.as_view(),
        name='detail'
    ),
    url(
        r'^detail/(?P<revision_id>[\w-]+)/(?P<file_path>.+)$',
        views.RevisionFileDetail.as_view(),
        name='file-detail'
    ),
    url(
        r'^send-for-approval/(?P<revision_id>[\w-]+)/$',
        views.SendForApproval.as_view(),
        name='send-for-approval'
    ),
    url(
        r'^preview/(?P<revision_id>[\w-]+)/$',
        views.Preview.as_view(),
        name='preview'
    ),
]
