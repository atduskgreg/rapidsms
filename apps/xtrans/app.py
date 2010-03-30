#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import rapidsms
from models import *
from datetime import datetime
import translators

import textonic

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
		#Take incoming message and create translation model.
		if self.method != 'off':
			entry = Translation(
				phone_number = message.connection.identity,
				original_message = message.text,
				)
			entry.save()
			#Check whether have enough messages to make a translation request.
			msg_load = self.check_msg_load()
			#Run translation request if there are enough messages.
			print "len(msg_load) = %s" % (len(msg_load))
			load_lim = 1
			if self.method == 'mturk':
				config = MTurkConfig.objects.get(current=True)
				load_lim = config.message_count
			if len(msg_load) <= load_lim:
				print "Submitting Translation"
				self.submit_translation(msg_load)
			print "added new message."
		return True

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
		"""Return the translation method currently being used by xtrans."""
		print self.method

	def check_msg_load(self):
		"""Check if the number of untranslated messages has reached the
		desired amount and initiate a translation if so."""
		config = MTurkConfig.objects.get(current=1)
		if config:
			msgs = Translation.objects.filter(translator_id=None)[:int(config.message_count)]
			if len(msgs) < config.message_count:
				return msgs
			else:
				print "Not enough messages"
				return []
		else:
			return []
			
	def submit_translation(self,msg_list):
		"""This method takes a list of messages to be translated and submits 
		translation based on the current translation method."""
		method = "_submit_" + self.method
		#Check for corresponding submit method
		if hasattr(self,method):
			return getattr(self,method)(msg_list)
		else:
			return "Method does not exist"
		
	def ajax_GET_transmethod(*args):
		"""Method to get called by ajax app, return the current 
		translation method.  Doesn't do anything yet."""
		#print args		

	def check_submissions(self):
		"""This method will select up to 5 untrabslated messages
		and run their respective _check_ methods.  It is called
		by the xtrans backend."""
		
		print "XTrans checking submissions."
		msg_list = Translation.objects.filter(translation=None)[:1]
		if len(msg_list) > 0:
			for msg in msg_list:
				self.check_for_results(msg)
			
	def check_for_results(self, trans):
		trans_method = "_check_" + trans.translation_method
		if hasattr(self,trans_method):
			return getattr(self,trans_method)(trans)
				
				
	"""These methods are the translation functions.
	They are called by name.  New _submit_ and _check_ methods
	can be easily added for new translation facilities."""

	def _submit_mturk(self,msg_list):
		"""This method creates an instance of the textonic HITGenerator
		and generated and submits a hit based on the current MTurkConfig 
		and message load."""
		print "Submitting to Mechanical Turk"
		config = MTurkConfig.objects.filter(current=True)[0]
		#Make message list that consistes of tuples containing message text and id.
		ql = []
		for msg in msg_list:
			ql.append((msg.original_message,msg.id))
		#Textonic HITGenerator.  Loaded with settings from current MTurkConfiguration
		options = [("This is an option","option_id")]
		aws_key = str(config.aws_key)
		aws_secret = str(config.aws_secret)
		hitter = textonic.HITGenerator(question_list = ql,
					       #answer_style = config.answer_style,
					       #answer_options = config.answer_options,
					       assignment_count = config.assignment_count,
					       #message_count = config.message_count,
					       overview_content = config.overview,
					       answer_options = options,
					       title = config.title,
					       description = config.description,
					       keywords = config.keywords,
					       reward = config.reward,
					       #lifetime = config.lifetime,
					       #duration = config.duration,
					       AWS_KEY =  aws_key,
					       AWS_SECRET = aws_secret,
					       )
		#Submit HIT
		sandbox = 'false'
		if config.sandbox:
			sandbox = 'true'
		res = hitter.SubmitHIT(sandbox=sandbox)
		print res[0].HITId
		for msg in msg_list:
			msg.translator_id = res[0].HITId
			msg.translation_method = 'mturk'
			msg.set_instructions(config)
			msg.save()

	def _check_mturk(self,msg):
		"""Method to check Mechanical Turk for completed HIT's.
		This method currently lack a way of deciding which translations
		to keep.  Each completed Hit contain message_count (default 5)
		translations from assignment_count (default 5) turkers."""
		#load MTurkConfig of current msg
		config = msg.get_instructions()
		sandbox = 'false'
		if config.sandbox:
			print "Playing in Sandbox"
			sandbox = 'true'
		#Check whether HIT has been completed
		hit_ret = mturk.HITRetriever(config.aws_key,config.aws_secret,sandbox)
		ret = hit_ret.SubmitHIT(sandbox=sandbox)
		if len(ret) == config.assignment_count:
			#Do something with translated messages.
			for ans in ret:
				for form in ans.answers[0]:
					question_id = form[1]
					answer = form[0]
					orig_msg = Translation.objects.get(id=question_id)
					orig_msg.translation = answer
					orig_msg.save()
					print "Got an answer to - %s - %s" % (orig_msg.original_message, answer)



#	def _submit_wwl(self,msg_list):
#		return 1
		
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

