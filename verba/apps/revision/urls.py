from django.conf.urls import url
from auth.decorators import login_required

from . import views

urlpatterns = [
    url(
        r'^$',
        login_required(views.RevisionList.as_view()),
        name='list'
    ),
]
