from django.conf.urls import url, include

urlpatterns = [
    url(r'^revision/', include('revision.urls', namespace='revision')),
]