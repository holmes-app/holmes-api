#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import UUID

from tornado.web import RequestHandler
from tornado import gen

from holmes.models import Review


class CreateViolationHandler(RequestHandler):

    @gen.coroutine
    def post(self, page_uuid, review_uuid):
        key = self.get_argument('key')
        title = self.get_argument('title')
        description = self.get_argument('description')
        points = int(self.get_argument('points'))

        parsed_uuid = None
        try:
            parsed_uuid = UUID(review_uuid)
        except ValueError:
            pass

        review = None
        if parsed_uuid:
            review = yield Review.objects.get(uuid=parsed_uuid)

        if not review:
            self.set_status(404, 'Review with uuid of %s not found!' % review_uuid)
            self.finish()
            return

        review.add_violation(key=key, title=title, description=description, points=points)
        yield review.save()

        self.write('OK')
        self.finish()
