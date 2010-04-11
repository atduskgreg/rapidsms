#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import os
from django.conf.urls.defaults import *
import xtrans.views as views

urlpatterns = patterns('',
                       url(r'^xtrans/?$',views.app_index),
                       url(r'^xtrans/messages/?$', views.messages_index),
                       url(r'^xtrans/messages/(?P<id>\d+)/view/?$', views.messages_view),
                       url(r'^xtrans/messages/(?P<id>\d+)/delete/?$', views.messages_delete),
                       url(r'^xtrans/config/create/?$', views.config_create),
                       url(r'^xtrans/config/submit/?$', views.config_submit),
                       url(r'^xtrans/config/view/?$',views.config_view),
                       url(r'^xtrans/config/?$', views.config_index),
                       url(r'^xtrans/config/(?P<id>\d+)/preview/?$', views.config_view),
                       url(r'^xtrans/config/(?P<id>\d+)/edit/?$', views.config_edit),
                       url(r'^xtrans/config/(?P<id>\d+)/delete/?$', views.config_delete),
                       url(r'^xtrans/toggle/on?$',views.toggle_on),
                       url(r'^xtrans/toggle/off?$',views.toggle_off),
)
