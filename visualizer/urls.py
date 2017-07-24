from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^logout$', views.sign_out, name='logout'),
    url(r'^$', views.index, name='index'),
]
