#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
from tornado import gen
from uuid import UUID
from ujson import dumps
from datetime import datetime, timedelta

from holmes.models.worker import Worker
from holmes.models.page import Page


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

    @gen.coroutine
    def get(self, uuid):
        worker_uuid = UUID(uuid)

        worker = yield Worker.objects.get(uuid=worker_uuid)
        if not worker:
            self.set_status(404, "Worker not found")
            self.finish()
            return

        yesterday = datetime.now() - timedelta(1)

        next_pages = yield Page.objects.filter(added_date__lt=yesterday).find_all()

        if not next_pages:
            self.set_status(404, "None available")
            self.finish()
            return

        next_page = next_pages[0]

        worker.current_page = next_page
        yield worker.save()
        next_page.updated_date = datetime.now()
        yield next_page.save()

        self.write(next_page.to_dict())
        self.finish()


class WorkersHandler(RequestHandler):

    @gen.coroutine
    def get(self):
        workers = yield Worker.objects.find_all()

        workers_json = []
        for worker in workers:
            #yield worker.load_references(['current_page'])
            workers_json.append(worker.to_dict())

        self.write(dumps(workers_json))
        self.finish()
