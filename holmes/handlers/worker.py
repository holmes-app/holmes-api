#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from tornado import gen

from holmes.models.worker import Worker
from holmes.handlers import BaseHandler


class WorkerHandler(BaseHandler):

    def post(self, worker_uuid, i_am='alive'):
        worker = Worker.by_uuid(worker_uuid, self.db)

        if worker:
            if i_am == 'alive':
                worker.last_ping = datetime.now()
            elif i_am == 'dead':
                self.db.delete(worker)
        else:
            self.db.add(Worker(uuid=worker_uuid))

        self.db.flush()

        self._remove_zombies_workers()
        self.db.flush()

        self.write(str(worker_uuid))
        self.finish()

    def _remove_zombies_workers(self):
        dt = datetime.now() - timedelta(seconds=self.application.config.ZOMBIE_WORKER_TIME)
        self.db.query(Worker).filter(Worker.last_ping < dt).delete()


class WorkersHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        workers = self.db.query(Worker).all()

        workers_json = [worker.to_dict() for worker in workers]
        self.write_json(workers_json)
        self.finish()
