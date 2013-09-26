#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
from tornado import gen
from uuid import UUID

from holmes.models.worker import Worker


class WorkerPingHandler(RequestHandler):

    @gen.coroutine
    def post(self):
        worker_uuid = UUID(self.get_argument('worker_uuid'))

        workers = yield Worker.objects.filter(uuid=worker_uuid).find_all()
        
        if len(workers) > 0:
            yield workers[0].save()
        else:
            yield Worker.objects.create(uuid=worker_uuid)
        
        self.write(str(worker_uuid))
        self.finish()
