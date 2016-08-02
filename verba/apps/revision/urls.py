from django.conf.urls import url
from auth.decorators import login_required

from . import views


urlpatterns = [
    url(
        r'^$',
        login_required(views.RevisionList.as_view()),
        name='list'
    ),
    url(
        r'^new/$',
        login_required(views.NewRevision.as_view()),
        name='new'
    ),
    url(
        r'^detail/(?P<revision_id>[\w-]+)/$',
        login_required(views.RevisionDetail.as_view()),
        name='detail'
    ),
    url(
        r'^detail/(?P<revision_id>[\w-]+)/(?P<file_path>.+)$',
        login_required(views.RevisionFileDetail.as_view()),
        name='file-detail'
    ),
    url(
        r'^send-for-approval/(?P<revision_id>[\w-]+)/$',
        login_required(views.SendForApproval.as_view()),
        name='send-for-approval'
    ),
    url(
        r'^preview/(?P<revision_id>[\w-]+)/$',
        login_required(views.Preview.as_view()),
        name='preview'
    ),
    url(
        r'^delete/(?P<revision_id>[\w-]+)/$',
        login_required(views.DeleteRevision.as_view()),
        name='delete'
    ),
]
