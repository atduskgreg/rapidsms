#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


import time
import Queue

from rapidsms.message import Message
from rapidsms.connection import Connection
from rapidsms.backends import Backend
import backend
from rapidsms import log
from rapidsms import utils

from apps.xtrans.models import *

POLL_INTERVAL = 60
LOG_LEVEL_MAP = {
    'traffic':'info',
    'read':'info',
    'write':'info',
    'debug':'debug',
    'warn':'warning',
    'error':'error'
}

class Backend(Backend):
    _title = "mturk"

    def configure(self, *args, **kwargs):
        if 'aws_key' in kwargs:
            self.AWS_KEY = kwargs.pop('aws_key')
            print self.AWS_KEY
        if 'aws_secret' in kwargs:
            self.AWS_SECRET = kwargs.pop('aws_secret')
            print self.AWS_SECRET
        if 'sandbox' in kwargs:
            self.sandbox = kwargs.pop('sandbox')
        else:
            self.sandbox = False
        
    def get_translation(self, **kwargs):
        hit_args = {}
        response = {}
        hit_kwargs['annotation'] = 'Annotation'
        hit_kwargs['hit_response'] = None
        if 'question_list' in kwargs:
            hit_args['question_list'] = kwargs.pop('question_list')
        else:
            response['status'] = 'error'
            response['value'] = 'no question specified'
            return response
        if 'answer_style' in kwargs:
            hit_args['answer_style'] = kwargs.pop('answer_style')
        else:
            response['status'] = 'error'
            response['value'] = 'no answer style specified'
            return response
        if 'answer_options' in kwargs:
            hit_args['answer_options'] = kwargs.pop('answer_options')
        else:
            response['status'] = 'error'
            response['value'] = 'no answer options specified'
            return response
        if 'title' in kwargs:
            hit_args['title'] = kwargs.pop('title')
        else:
            response['status'] = 'error'
            response['value'] = 'no title specified'
            return response
        if 'description' in kwargs:
            hit_args['description'] = kwargs.pop('description')
        else:
            response['status'] = 'error'
            response['value'] = 'no desciption specified'
            return response
        if 'keywords' in kwargs:
            hit_args['keywords'] = kwargs.pop('keywords')
        else:
            response['status'] = 'error'
            response['value'] = 'no keywords specified'
            return response
        if 'reward' in kwargs:
            hit_args['reward'] = kwargs.pop('reward')
        else:
            response['status'] = 'error'
            response['value'] = 'no reward specified'
            return response
        if 'lifetime' in kwargs:
            hit_args['lifetime'] = kwargs.pop('lifetime')
        else:
            response['status'] = 'error'
            response['value'] = 'no lifetime specified'
            return response
        if 'assignment_count' in kwargs:
            hit_kwargs['assignment_count'] = kwargs.pop('assignment_count')
        else:
            response['status'] = 'error'
            response['value'] = 'no assignment count specified'
            return response
        if 'duration' in kwargs:
            hit_args['duration'] = kwargs.pop('duration')
        else:
            response['status'] = 'error'
            response['value'] = 'no duration specified'
            return response
        if 'approval_delay' in kwargs:
            hit_args['approval_delay'] = kwargs.pop('approval_delay')
        else:
            response['status'] = 'error'
            response['value'] = 'no approval delay specified'
            return response
        return _submitHIT(hit_args)
        
    def _submitHIT(self, _hit_args):
        hit_gen = textonic.HITGenerator(AWS_KEY=self.AWS_KEY,
                                        AWS_SECRET=self.AWS_SECRET,
                                        question_list=_hit_args['question_list'],
                                        answer_style=_hit_args['answer_style'],
                                        answer_options=_hit_args['answer_options'],
                                        title=_hit_args['title'],
                                        annotation=_hit_args['annotation'],
                                        description=_hit_args['desciption'],
                                        keywords=_hit_args['keywords'],
                                        reward=_hit_args['reward'],
                                        lifetime=_hit_args['lifetime'],
                                        assignment_count=_hit_args['assignmen_count'],
                                        duration=_hit_args['assignment_count'],
                                        approval_delay=_hit_args['approval_delay'],
                                        hit_response=_hit_args['hit_response'])
        return hit_gen.SubmitHIT(sandbox=sandbox)

    def run(self):
        hit_id = 0
        hit_ret = textonic.HITRetriever(self.AWS_KEY,self.AWS_SECRET,hit_id)

    def start(self):
        print "MTurk starting."
        backend.Backend.start(self)

    def stop(self):
        backend.Backend.stop(self)
