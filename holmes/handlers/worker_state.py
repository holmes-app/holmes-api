#!/usr/bin/python
# -*- coding: utf-8 -*-

from ujson import loads
from tornado.web import RequestHandler
from tornado import gen

from holmes.models.worker import Worker
from holmes.models.review import Review


class WorkerStateHandler(RequestHandler):

    @gen.coroutine
    def post(self, worker_uuid, review_uuid, state):
        worker = yield Worker.objects.get(uuid=worker_uuid)

        if not worker:
            self.set_status(404, 'Unknown Worker')
            self.finish()
            return

        review = yield Review.objects.get(uuid=review_uuid)

        if not review:
            self.set_status(404, 'Unknown Review')
            self.finish()
            return

        if 'start' == state:
            if review.is_complete:
                self.set_status(400, 'Review already completed')
                self.finish()
                return

            worker.current_review = review

        if 'complete' == state:
            if self.request.body:
                post_data = loads(self.request.body)
                error = post_data['error']
                if error:
                    review.failure_message = error
                    yield review.save()

            worker.current_review = None

        yield worker.save()

        self.write('OK')
        self.finish()


