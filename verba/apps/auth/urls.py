from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^callback/$', views.CallbackView.as_view(), name='callback'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
]
