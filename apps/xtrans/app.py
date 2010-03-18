#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import rapidsms
from models import *
from datetime import datetime
import translators

class App (rapidsms.app.App):

	def start (self):
		"""Configure your app in the start phase."""
		#This is the default translation method from the tranlators.py file.
		self.method = translators.default
		pass
	
	def parse (self, message):
		"""Parse and annotate messages in the parse phase."""
		pass
	
	def handle (self, message):
		"""Add your main application logic in the handle phase."""
		if self.method != 'off':
			entry = Translation(
				phone_number = message.connection.identity,
				original_message = message.text,
				translation_method = self.method,
				)
			entry.save()
			#Check whether have enough messages to make a translation request.
			msg_load = check_msg_load()
			#Run translation request if there are enough messages.
			if len(msg_load) > 1:
				translate(msg_load)

	def cleanup (self, message):
		"""Perform any clean up after all handlers have run in the
		cleanup phase."""
		pass
	
	def outgoing (self, message):
		"""Handle outgoing message notifications."""
		pass
	
	def stop (self):
		"""Perform global app cleanup when the application is stopped."""
		pass

	def method(self):
		print "You Got Me"

	def check_msg_load(self):
		config = MTurkConfig.objects.get(current=1)
		if config:
			msgs = Translation.objects.filter(translator_id=None)[:int(config.message_count)]
			if len(msgs) < config.message_count:
				return msgs
			else:
				return ['Not Enought Messages']
		else:
			return ['No Configuration']
			
	def translate(self,msg_list):
		if hasattr(self,self.method):
			return getattr(self,self.method)(msg_list)
		else:
			return "Method does not exist"
		
	def ajax_GET_transmethod(*args):
		print args
			
	"""These methods are the translation functions.
	They are called by name.  To add a new one simply add
	a method that takes an argument for the model id."""
		
	def mturk(self,msg_list):
		mturk_backend = self.router.get_backend('mturk')
		config = MTurkConfig.objects.filter(current=True)[0]
		response = mturk_backend.get_translation(question_list = msg_list,
							 answer_style = config.answer_style,
							 answer_options = config.answer_options,
							 assignment_count = config.assignment_count,
							 message_count = config.message_count,
							 title = config.title,
							 description = config.description,
							 keywords = config.keywords,
							 reward = config.reward,
							 lifetime = config.lifetime,
							 duration = config.duration,
							 AWS_KEY = user.AWS_KEY,
							 AWS_SECRET = user.AWS_SECRET,
							 sandbox = config.sandbox,
							 )
		for i in msg_list:
			trans = Translation.objects.get(id=i[1])
			trans.translator_id = response
			trans.save()
		
		
	def wwl(self,msg_list):
		return 1
		
	def meedan(self,msg_list):
		return 1
	
	def human(self,msg_list):
		return 1
	
