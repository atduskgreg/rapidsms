#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.webui.utils import render_to_response
from models import *
from datetime import datetime, timedelta
from django import forms
from django.http import HttpResponseRedirect
from django.http import HttpResponse
import translators

def config(req):
    template_path = "xtrans/config.html"
    form = ConfigForm()
    return render_to_response(req, template_path, {'form' : form})

def config_submit(req):
    form = req.POST
    print form['title']
    

def config_create(req):
    c = MTurkConfig()
    f = ConfigForm(instance=c)
    template_path = "xtrans/mturk_config.html"
    return render_to_response(req, template_path, {'form':f})

def config_view(req):
    c = MTurkConfig.objects.filter(current=True)
    if c:
        f = ConfigForm(instance=c)
        template_path = "xtrans/mturk_config.html"
        return render_to_respone(req, template_path, {'form':f})
    else:
        c = MTurkConfig()
        f = ConfigForm(instance=c)
        template_path = "xtrans/mturk_config.html"
        return render_to_response(req, template_path, {'form':f})

def app_index(req):
    current_method = get_current_method()
    method = ''
    if(current_method != 'off'):
        status = 'On'
        is_on = True
        method = translators.methods[current_method]
    else:
        status = 'Off'
        is_on = False
    all_methods = get_all_methods()
    template_path = "xtrans/index.html"
    return render_to_response(req, template_path, locals())

def toggle_on(req):
    return toggle(req,True)

def toggle_off(req):
    return toggle(req,False)

def toggle(req,status):
    if(status):
        status = 'On'
    else:
        status = 'Off'
    template_path = "xtrans/index.html"
    return render_to_response(req, template_path, {'status':status})

def get_current_method():
    return 'mturk'

def get_all_methods():
    return 'holder'
	
