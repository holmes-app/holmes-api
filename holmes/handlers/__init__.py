#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.web import RequestHandler


class BaseHandler(RequestHandler):
    def options(self):
        self.set_header('Access-Control-Allow-Origin', self.application.config.ORIGIN)
        self.set_header('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        self.set_header('Access-Control-Allow-Headers', 'Accept, Content-Type')
        self.set_status(200)
        self.finish()

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', self.application.config.ORIGIN)
        self.set_header('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
