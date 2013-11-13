#!/usr/bin/python
# -*- coding: utf-8 -*-

from ujson import loads

from holmes.models.worker import Worker
from holmes.models.review import Review
from holmes.handlers import BaseHandler


class WorkerStateHandler(BaseHandler):

    def post(self, worker_uuid, review_uuid, state):
        worker = Worker.by_uuid(worker_uuid, self.db)

        if not worker:
            self.set_status(404, 'Unknown Worker')
            self.finish()
            return

        review = Review.by_uuid(review_uuid, self.db)

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

            self.db.flush()

            worker.current_review.page.last_review = review
            self.db.flush()

            worker.current_review = None

        self.db.flush()

        self.write('OK')
        self.finish()
