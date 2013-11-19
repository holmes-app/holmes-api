#!/usr/bin/python
# -*- coding: utf-8 -*-

from ujson import dumps

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
            if not url:
                self.set_status(400, 'Invalid URL')
                self.finish()
                return

            worker.current_url = url

        if 'complete' == state:
            worker.current_url = None

        self.db.flush()

        self.application.event_bus.publish(dumps({
            'type': 'worker-status',
            'workerId': str(worker.uuid)
        }))

        self.write('OK')
        self.finish()
