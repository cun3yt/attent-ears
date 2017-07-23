from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^logout$', views.sign_out, name='logout'),
    url('socialcomplete/google-oauth2', views.social_complete_google, name='social_complete_google'),
    url(r'^$', views.index, name='index'),
]
