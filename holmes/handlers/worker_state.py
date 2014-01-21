#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from ujson import dumps
import tornado.web

from holmes.models.worker import Worker
from holmes.handlers import BaseHandler
from holmes.redis_lock import RedisLock


class WorkerStateHandler(BaseHandler):

    @tornado.web.asynchronous
    def post(self, worker_uuid, state):
        worker = Worker.by_uuid(worker_uuid, self.db)

        if not worker:
            self.set_status(404, 'Unknown Worker')
            self.finish()
            return

        if 'start' == state:
            url = self.request.body
            if not url:
                logging.warning('Invalid URL trying to start worker %s.' % worker_uuid)
                raise tornado.web.HTTPError(400, 'Invalid URL', reason='Invalid URL')

            self.start_work(worker, url)
            return

        elif 'complete' == state and worker.current_url is not None:
            self.complete_work(worker, worker.current_url)
            worker.current_url = None

        else:
            logging.warning('Invalid operation (not start nor complete) in worker %s (current url: %s).' % (
                worker_uuid, worker.current_url
            ))
            #raise tornado.web.HTTPError(400, 'Invalid Operation', reason='Invalid Operation')

    def start_work(self, worker, url):
        lock = RedisLock(
            self.application.redis,
            lock_key="redis-lock-%s" % url,
            lock_timeout=self.application.config.ZOMBIE_WORKER_TIME)

        lock.acquire(self.handle_lock_acquired(worker, url))

    def handle_lock_acquired(self, worker, url):
        def handle(acquired):
            if acquired:
                worker.current_url = url
                self.db.flush()

                self.application.event_bus.publish(dumps({
                    'type': 'worker-status',
                    'workerId': str(worker.uuid)
                }))

                self.write('OK')
                self.finish()
            else:
                self.write("NOK")
                self.finish()

        return handle

    def complete_work(self, worker, url):
        lock = RedisLock(
            self.application.redis,
            lock_key="redis-lock-%s" % url,
            lock_timeout=self.application.config.ZOMBIE_WORKER_TIME)

        lock.release(self.handle_lock_released(worker, url))

    def handle_lock_released(self, worker, url):
        def handle(deleted_count):
            worker.current_url = None
            self.db.flush()

            self.application.event_bus.publish(dumps({
                'type': 'worker-status',
                'workerId': str(worker.uuid)
            }))

            self.write('OK')
            self.finish()

        return handle
