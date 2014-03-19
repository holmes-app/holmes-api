#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa

from holmes.models.worker import Worker
from holmes.handlers import BaseHandler


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
