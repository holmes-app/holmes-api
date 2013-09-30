#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import UUID

from tornado.web import RequestHandler
from tornado import gen
from ujson import dumps

from holmes.models import Review


class ReviewHandler(RequestHandler):

    @gen.coroutine
    def get(self, page_uuid, review_uuid):
        parsed_uuid = None
        try:
            parsed_uuid = UUID(review_uuid)
        except ValueError:
            pass

        review = None
        if parsed_uuid:
            review = yield Review.objects.get(uuid=parsed_uuid)

        if not review:
            self.set_status(404, "Review with uuid of %s not found!" % review_uuid)
            self.finish()
            return

        yield review.load_references(['page'])
        yield review.page.load_references(['domain'])

        self.write(dumps(review.to_dict()))
        self.finish()
