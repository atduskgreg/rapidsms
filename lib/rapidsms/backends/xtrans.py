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

class Backend(Backend):
    """The sole purpose of this backend is to trigger the 
    xtrans app to check for completed translations."""
    _title = "xtrans"

    def configure(self, *args, **kwargs):
        self.interval = 20
        self.timeout = 10
        self.log_level = 'debug'
        self.router.log(self.log_level,"XTrans backend ON")

    def run(self):
        while self._running:
            self.router.log(self.log_level,"XTrans backend says hello.")
            for app in self.router.apps:
                if app.slug == 'xtrans':
                    app.check_submissions()
            time.sleep(self.interval)

    def start(self):
        self.router.log(self.log_level,"XTrans backend starting.")
        backend.Backend.start(self)

    def stop(self):
        backend.Backend.stop(self)
