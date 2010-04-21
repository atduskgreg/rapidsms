#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import rapidsms
from models import *
from datetime import datetime
import translators
#from wwlapi.wwl import wwl

class App (rapidsms.app.App):

#	def __init__(self):
#		"""Initialize translators.  Was getting errors in start."""
#		self.method = translators.default
#		#Exclude self.debug to quiet.
#		self.MTurkManager = MTurkManger(5,self.debug)

	def start (self):
		"""Configure your app in the start phase."""
		#This is the default translation method from the tranlators.py file.
#		self.wwl = wwl()
		self.debug("MTurk: Init message.")
		self.method = translators.default
		self.MTurkManager = MTurkManager(50,debug=self.debug,router=self.router)

	def parse (self, message):
		"""Parse and annotate messages in the parse phase."""
		pass
	
	def handle (self, message):
		"""Add your main application logic in the handle phase."""
		#Take incoming message and create translation model.
		if self.method != 'off':
			entry = Translation(
				phone_number = message.connection.identity,
				original_message = message.text,
				)
			entry.save()
			self.debug("XTrans: new message received.")
			#Check whether have enough messages to make a translation request.
			self.submit_translation(entry.id)
		#backend = self.router.get_backend('pygsm')
		#backend.message('+19173183238','sending you a message').send()

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
		
	def submit_translation(self, entry_id):
		"""Request translation using the current method."""
		if self.method:
			method = "_submit_" + self.method
	 	        #Check for corresponding submit method
			if hasattr(self,method):
				getattr(self,method)(entry_id)
			
	def ajax_GET_transmethod(*args):
		"""Method to get called by ajax app, return the current 
		translation method.  Doesn't do anything yet."""
		#print args		

	def check_submissions(self):
		"""This method will select up to 5 untranslated messages
		and run their respective _check_ methods.  It is called
		by the xtrans backend."""
		self.debug("XTrans: check_submissions called.")
		try:
			method = '_check_' + self.method
			if hasattr(self,method):
				getattr(self,method)()
		#Silly workaround for check_submissions being called before start()
		except AttributeError:
			self.debug("check_submissions called before init.")

	def _submit_mturk(self,entry_id):
		"""Notify the Mechanical Turk Manager of a new message."""
		self.debug("Notifying Mechanical Turk of new message.")
		self.MTurkManager.new_message(entry_id)

	def _check_mturk(self):
		"""Method to check Mechanical Turk for completed HIT's.
		This method currently lack a way of deciding which translations
		to keep.  Each completed Hit contain message_count (default 5)
		translations from assignment_count (default 5) turkers."""
		self.debug("XTrans: checking submissions.")
		self.MTurkManager.check_submissions()
	
#	def _submit_wwl(self,entry_id):
#		wwl.get()
		
#	def _check_wwl(self,msg_id):
#		return 1

#	def _submit_meedan(self,msg_list):
#		return 1

#	def _check_meedan(self,msg_id):
#		return 1
	
#	def _submit_human(self,msg_list):
#		return 1
	
#	def _check_human(self,msg_id):
#		return 1

