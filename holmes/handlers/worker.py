#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from ujson import dumps

import sqlalchemy as sa

from holmes.models.worker import Worker
from holmes.handlers import BaseHandler


class WorkerHandler(BaseHandler):

    def post(self, worker_uuid, i_am='alive'):
        self._remove_zombie_workers()

        worker = Worker.by_uuid(worker_uuid, self.db)

        if worker:
            if i_am == 'alive':
                worker.last_ping = datetime.now()
            elif i_am == 'dead':
                self.db.delete(worker)
        else:
            worker = Worker(uuid=worker_uuid)
            self.db.add(worker)

        self.db.flush()

        self.application.event_bus.publish(dumps({
            'type': 'worker-status',
            'workerId': str(worker.uuid)
        }))

        self.write(str(worker_uuid))

    def _remove_zombie_workers(self):
        self.db.flush()

        dt = datetime.now() - timedelta(seconds=self.application.config.ZOMBIE_WORKER_TIME)

        workers_to_delete = self.db.query(Worker).filter(Worker.last_ping < dt).order_by(Worker.id).all()

        for worker in workers_to_delete:
            self.db.delete(worker)

        self.db.flush()


class WorkersHandler(BaseHandler):

    def get(self):
        workers = self.db.query(Worker).all()

        workers_json = [worker.to_dict() for worker in workers]
        self.write_json(workers_json)


class WorkersInfoHandler(BaseHandler):

    def get(self):
        total_workers = self.db \
            .query(sa.func.count(Worker.id).label('count')) \
            .one()

        inactive_workers = self.db \
            .query(sa.func.count(Worker.id).label('count')) \
            .filter(Worker.current_url == None) \
            .one()

        workers_info = {
            'total': total_workers.count,
            'inactive': inactive_workers.count,
            'active': total_workers.count - inactive_workers.count,
        }
        self.write_json(workers_info)
