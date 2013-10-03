#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
from tornado import gen
from uuid import UUID
from ujson import dumps

from holmes.models.worker import Worker


class WorkerHandler(RequestHandler):

    @gen.coroutine
    def post(self, uuid):
        worker_uuid = UUID(uuid)

        worker = yield Worker.objects.get(uuid=worker_uuid)

        if worker:
            yield worker.save()
        else:
            yield Worker.objects.create(uuid=worker_uuid)

        self.write(str(worker_uuid))
        self.finish()


class WorkersHandler(RequestHandler):

    @gen.coroutine
    def get(self):
        workers = yield Worker.objects.find_all()

        workers_json = []
        for worker in workers:
            workers_json.append(worker.to_dict())

        self.write(dumps(workers_json))
        self.finish()
