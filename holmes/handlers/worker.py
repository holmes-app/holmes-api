#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from tornado import gen
from uuid import UUID

from holmes.models.worker import Worker
from holmes.handlers import BaseHandler


class WorkerHandler(BaseHandler):

    def post(self, uuid, i_am='alive'):
        worker_uuid = UUID(uuid)

        worker = Worker.by_uuid(worker_uuid, self.db)

        if worker:
            if i_am == 'alive':
                worker.last_ping = datetime.now()
            elif i_am == 'dead':
                self.db.delete(worker)
        else:
            self.db.add(Worker(uuid=worker_uuid))

        self._remove_zombies_workers()
        self.db.flush()

        self.write(str(worker_uuid))
        self.finish()

    @gen.coroutine
    def _remove_zombies_workers(self):
        dt = datetime.now() - timedelta(seconds=self.application.config.ZOMBIE_WORKER_TIME)
        self.db.query(Worker).filter(Worker.last_ping < dt).delete()


class WorkersHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        workers = self.db.query(Worker).all()

        workers_json = []
        for worker in workers:
            worker_dict = worker.to_dict()

            if worker.working:
                page = worker.current_review.page
                if page:
                    worker_dict['page_url'] = page.url
                    worker_dict['page_uuid'] = str(page.uuid)
            workers_json.append(worker_dict)

        self.write_json(workers_json)
        self.finish()
