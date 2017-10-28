from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^logout$', views.sign_out, name='logout'),
    url(r'^settings$', views.settings, name='settings'),
    url(r'^oauth/outreach-redirect$', views.outreach_redirect, name='outreach-redirect'),
    url(r'^oauth/salesforce-redirect$', views.salesforce_redirect, name='salesforce-redirect'),
    url(r'^slack-interface/slack-command$', views.slack_command, name='slack_command'),
    url(r'^$', views.index, name='index'),
]