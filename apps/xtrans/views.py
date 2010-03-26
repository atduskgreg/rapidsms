#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.webui.utils import render_to_response
from models import *
from datetime import datetime, timedelta
from django import forms
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.template import Template
import translators

def config_submit(req):
    """Handle a new Configuration form."""
    form = req.POST
    new_config = MTurkConfig()
    config_change = 0
    print form
    for i in form:
        if hasattr(new_config,i):
            config_change = 1
            new_field = ''
            if i == 'current':
                if form[i] == 'on':
                    print "Setting Current to True."
                    new_field = True
                else:
                    new_field = False
            else:
                new_field = form[i]
            setattr(new_config,i,new_field)
    if config_change == 1:
        print "saving"
        new_config.save()
    template_path = "xtrans/mturk_submit.html"
    return render_to_response(req, template_path, {})
#    print form['title']
    

def config_create(req):
    """Create a new configuration"""
    c = MTurkConfig()
    f = ConfigForm(instance=c)
    template_path = "xtrans/mturk_config.html"
    return render_to_response(req, template_path, {'form':f})

def config_view(req):
    """View current configuration"""
    c = MTurkConfig.objects.filter(current=True)
    if c:
        if c[0].overview is not None:            
            content = c[0].overview
        else:
            content = "Hello.  No Content."
        template_path = "xtrans/mturk_view.html"
        return render_to_response(req, template_path, {'content':content})
        #return HttpResponse(content)
    else:
            f = ConfigForm(instance=c)
            template_path = "xtrans/mturk_config.html"
            return render_to_response(req, template_path, {'form':f})

def app_index(req):
    #This will not be hard coded.
    current_method = 'mturk'
    method = ''
    if(current_method != 'off'):
        status = 'On'
        is_on = True
        method = translators.methods[current_method]
    else:
        status = 'Off'
        is_on = False
    template_path = "xtrans/index.html"
    return render_to_response(req, template_path, locals())

"""These methods are meant to be called by way of the ajax app
as a method for turning the system on and off"""

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


	
