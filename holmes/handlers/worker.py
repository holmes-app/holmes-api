#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
from tornado import gen
from uuid import UUID
from ujson import dumps

from holmes.models.worker import Worker


class WorkerHandler(RequestHandler):

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

    @gen.coroutine
    def get(self):
        workers = yield Worker.objects.filter().find_all()

        workers_json = []
        for worker in workers:
            workers_json.append(worker.to_dict())

        self.write(dumps(workers_json))
        self.finish()
