#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.web import RequestHandler


class WorkerPingHandler(RequestHandler):
    def post(self):
        worker_uuid = self.get_argument('worker_uuid', '')

        self.write(worker_uuid)
        self.finish()
