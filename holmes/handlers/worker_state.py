#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.models.worker import Worker
from holmes.handlers import BaseHandler


class WorkerStateHandler(BaseHandler):

    def post(self, worker_uuid, state):
        worker = Worker.by_uuid(worker_uuid, self.db)

        if not worker:
            self.set_status(404, 'Unknown Worker')
            self.finish()
            return

        if 'start' == state:
            url = self.request.body
            worker.current_url = url

        if 'complete' == state:
            worker.current_url = None

        self.db.flush()

        self.write('OK')
        self.finish()
