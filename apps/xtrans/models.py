#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.forms import ModelForm
from datetime import datetime
from rapidsms.message import Message

class AWSUser(models.Model):
    aws_key = models.CharField(max_length=100, null=False)
    aws_secret = models.CharField(max_length=100,null=False)
    identifier = models.CharField(max_length=100,null=False)

    def __unicode__(self):
        return self.identifier

class MTurkConfig(models.Model):
    aws_key = models.CharField(max_length=100, null=False)
    aws_secret = models.CharField(max_length=100,null=False)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    keywords = models.CharField(max_length = 200)
#    request = models.TextField()
    overview = models.TextField()
    reward = models.CharField(max_length=20,default="0.25")
#    answer_style = models.SlugField()
#    answer_options = models.CharField(max_length=200)
#    lifetime = models.CharField(max_length=200)
#    duration = models.CharField(max_length=200)
#    current = models.BooleanField(null=False, default=False)
    assignment_count = models.CharField(max_length=20, default="5")
    message_count = models.CharField(max_length=20, default="5")
    order = models.CharField(max_length=10,default="0")
    numeric = models.BooleanField(null=False, default=False)
    sandbox = models.BooleanField(null=False, default=False)

    @classmethod 
    def make_current(modelBase, config):
        for m in MTurkConfig.objects.all():
            m.current = False
            m.save()
        config.current = True

	

    def __unicode__(self):
        return self.title

    class Meta:
        db_table = u'configuration'

class ConfigForm(ModelForm):
    class Meta:
        model = MTurkConfig
        #exclude['']

"""This is the model for translating incoming messages.
	It holds the sender's number, the time it was created,
	the original, the name of the translation method, an 
	optional translator id as well as an optional foreign key
	to another model"""

class Translation(models.Model):
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    received_at = models.DateTimeField(default=datetime.now)
    original_message = models.TextField(null=False) 
    translation_method = models.SlugField() #method being used
    translator_id = models.CharField(max_length=64, blank=True,null=True,default=None)
    translator_config = models.PositiveIntegerField(blank=True,null=True,default=None)
    translation = models.TextField(null=True, default=None)

    @classmethod
    def has_been_translated(self):
        return self.translation != None

