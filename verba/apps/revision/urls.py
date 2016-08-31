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
    url(
        r'^(?P<revision_id>\d+)/send-for-2i/$',
        login_required(views.SendFor2i.as_view()),
        name='send-for-2i'
    ),
    url(
        r'^(?P<revision_id>\d+)/send-back/$',
        login_required(views.SendBack.as_view()),
        name='send-back'
    ),
    url(
        r'^(?P<revision_id>\d+)/publish/$',
        login_required(views.Publish.as_view()),
        name='publish'
    ),
    url(
        r'^(?P<revision_id>\d+)/activities/$',
        login_required(views.Activities.as_view()),
        name='activities'
    ),
    url(
        r'^(?P<revision_id>\d+)/changes/$',
        login_required(views.Changes.as_view()),
        name='changes'
    ),
]
