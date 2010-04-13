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
            if i == 'order':
                new_field = form[i]
                others = MTurkConfig.objects.filter(order=new_field)
                if others:
                    for o in others:
                        if o.order==new_field:
                            o.order = 0
                            o.save()
#                if form[i] == 'on':
#                    print "Setting Current to True."
#                    new_field = True
#                else:
#                    new_field = False
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
    return render_to_response(req, template_path, {'form':f,'edit':None})

def config_view(req,id=None):
    """View current configuration"""
    if id:
        c = MTurkConfig.objects.get(id=id)
        if c.overview is not None:
            content = c.overview
        else:
            content = "Hello, No Content"
    else:
        c = MTurkConfig.objects.filter(count="0")
        if c:
            if c[0].overview is not None:            
                content = c[0].overview
            else:
                content = "Hello.  No Content."
        else:
            c = MTurkConfig()
            f = ConfigForm(instance=c)
            template_path = "xtrans/mturk_config.html"
            return render_to_response(req, template_path, {'form':f,'edit':None})
    template_path = "xtrans/mturk_view.html"
    return render_to_response(req, template_path, {'content':content})
        #return HttpResponse(content)

def config_index(req):
    template_path = "xtrans/configs/index.html"
    all = MTurkConfig.objects.all()
    return render_to_response(req,template_path,{'configs':all})

def config_edit(req,id=None):
    form = ConfigForm(req.POST or None,
                      instance=id and MTurkConfig.objects.get(id=id))

    if req.method == 'POST' and form.is_valid():
        form.save()
        #template_path = "xtrans/configs/index.html"
        #return render_to_response(req,template_path,{})
        return config_index(req)
    template_path = "xtrans/mturk_config.html"
    return render_to_response(req,template_path,{'form':form,'edit':id})
#    if req.method == "POST":
#        form = req.post
#        template_path = "xtrans/mturk_submit"
#       print form.id
#        return render_to_response(req,template_path,{})
#    template_path = "xtrans/mturk_config.html"
#    c = MTurkConfig.objects.get(id=id)
#    form = ConfigForm(instance=c)
#    print form
#    return render_to_response(req,template_path,{'form':c,'edit':1})
    


def config_delete(req,id):
    template_path = "xtrans/configs/index.html"
    c = MTurkConfig.objects.get(id=id)
    c.delete()
    all = MTurkConfig.objects.all()
    return render_to_response(req,template_path,{'config':all})

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

def messages_index(req):
    template_path = "xtrans/messages/index.html"
    all = Translation.objects.order_by('received_at').reverse()
    return render_to_response(req, template_path, {'messages':all})

def messages_view(req,id):
    template_path = "xtrans/messages/view.html"
    msg = Translation.objects.get(id=id)
    return render_to_response(req, template_path, {'msg':msg})

def messages_delete(req,id):
    msg = Translation.objects.get(id=id)
    msg.delete()
    return messages_index(req)

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


	
