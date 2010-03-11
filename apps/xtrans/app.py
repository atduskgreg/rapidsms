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
			result = translate(entry.id)
			
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
		
	def translate(self,msg_id):
		if hasattr(self,self.method):
			return getattr(self,self.method)(msg_id)
		else:
			return "Method does not exist"
		
	def ajax_GET_transmethod(*args):
		print args
			
	"""These methods are the translation functions.
	They are called by name.  To add a new one simply add
	a method that takes an argument for the model id."""
		
	def mturk(self,msg_id):
		mturk_backend = self.router.get_backend('mturk')
		msg = Translation.objects.filter(id=msg_id)

		if msg.has_been_translater():
			return "ready"
		else:
			config = MTurkConfig.objects.filter(current=True)
			user = AWSUser.objects.filter(id=config.AWS_user)
			response = mturk_backend.get_translation(question_list = config.request + '\n' + msg.original_message,
								 answer_style = config.answer_style,
								 answer_options = config.answer_options,
								 assignment_count = config.assignment_count,
								 title = config.title,
								 annotation = 'Annotation',
								 description = config.description,
								 keywords = config.keywords,
								 reward = config.reward,
								 lifetime = config.lifetime,
								 duration = config.duration,
								 approval_delay = config.approbal_delay,
								 AWS_KEY = user.AWS_KEY,
								 AWS_SECRET = user.AWS_SECRET,
								 sandbox = config.sandbox,
								 )
								 
		
		
	def wwl(self,msg_id):
		return 1
		
	def meedan(self,msg_id):
		return 1
	
	def human(self,msg_id):
		return 1
	
