#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from uuid import UUID

import logging
from tornado.web import RequestHandler
from tornado import gen
from ujson import dumps
from motorengine import Q

from holmes.models import Review


class BaseReviewHandler(RequestHandler):
    def _parse_uuid(self, uuid):
        try:
            return UUID(uuid)
        except ValueError:
            return None


class ReviewHandler(BaseReviewHandler):
    @gen.coroutine
    def get(self, page_uuid, review_uuid):
        review = None
        if self._parse_uuid(review_uuid):
            review = yield Review.objects.get(uuid=review_uuid)

        if not review:
            self.set_status(404, 'Review with uuid of %s not found!' % review_uuid)
            self.finish()
            return

        yield review.load_references(['page'])
        yield review.page.load_references(['domain'])

        self.write(dumps(review.to_dict()))
        self.finish()


class CompleteReviewHandler(BaseReviewHandler):
    @gen.coroutine
    def post(self, page_uuid, review_uuid):
        review = None
        if self._parse_uuid(review_uuid):
            review = yield Review.objects.get(uuid=review_uuid)

        if not review:
            self.set_status(404, 'Review with uuid of %s not found!' % review_uuid)
            logging.debug('Review with uuid of %s not found!' % review_uuid)
            self.finish()
            return

        if review.is_complete:
            self.set_status(400, 'Review with uuid %s is already completed!' % review_uuid)
            logging.debug('Review with uuid %s is already completed!' % review_uuid)
            self.finish()
            return

        review.is_complete = True
        review.is_active = True
        review.completed_date = datetime.now()
        error = self.get_argument('error', default=None)
        if error:
            review.failure_message = error

        yield review.load_references(['page'])
        review.page.last_review = review
        yield review.page.save()

        yield review.save()

        query = Q(page=review.page) & Q(uuid__ne=review_uuid)

        yield Review.objects.filter(query).update({
            Review.is_active: False
        })

        self.write('OK')
        self.finish()
