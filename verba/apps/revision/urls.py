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
        r'^(?P<revision_id>\d+)/editor/$',
        login_required(views.Editor.as_view()),
        name='editor'
    ),
    url(
        r'^(?P<revision_id>\d+)/editor/(?P<file_path>.+)/$',
        login_required(views.EditFile.as_view()),
        name='edit-file'
    ),
]
