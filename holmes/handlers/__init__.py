#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from ujson import dumps
from tornado.web import RequestHandler

from holmes import __version__


class BaseHandler(RequestHandler):
    def initialize(self, *args, **kw):
        super(BaseHandler, self).initialize(*args, **kw)
        self._session = None

    def log_exception(self, typ, value, tb):
        for handler in self.application.error_handlers:
            handler.handle_exception(
                typ, value, tb, extra={
                    'url': self.request.full_url(),
                    'ip': self.request.remote_ip,
                    'holmes-version': __version__
                }
            )

        super(BaseHandler, self).log_exception(typ, value, tb)

    def on_finish(self):
        if self.application.config.COMMIT_ON_REQUEST_END:
            if self.get_status() > 399:
                logging.debug('ROLLING BACK TRANSACTION')
                self.db.rollback()
            else:
                logging.debug('COMMITTING TRANSACTION')
                self.db.flush()
                self.db.commit()
                self.application.event_bus.flush()

    def options(self):
        self.set_header('Access-Control-Allow-Origin', self.application.config.ORIGIN)
        self.set_header('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        self.set_header('Access-Control-Allow-Headers', 'Accept, Content-Type, X-AUTH-HOLMES')
        self.set_status(200)
        self.finish()

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', self.application.config.ORIGIN)
        self.set_header('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')

    def write_json(self, obj):
        self.set_header("Content-Type", "application/json")
        self.write(dumps(obj))

    @property
    def cache(self):
        return self.application.cache

    @property
    def db(self):
        return self.application.db

    @property
    def girl(self):
        return self.application.girl

