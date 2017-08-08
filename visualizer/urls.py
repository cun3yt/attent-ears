from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^logout$', views.sign_out, name='logout'),
    url(r'^settings$', views.settings, name='settings'),
    url(r'^outreach-redirect$', views.outreach_redirect, name='outreach-redirect'),
    url(r'^$', views.index, name='index'),
]
