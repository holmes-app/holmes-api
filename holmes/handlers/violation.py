#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import UUID

from tornado.web import RequestHandler
from tornado import gen

from holmes.handlers import BaseHandler
from holmes.models import Review, Violation


class CreateViolationHandler(RequestHandler):

    @gen.coroutine
    def post(self, page_uuid, review_uuid):
        key = self.get_argument('key')
        title = self.get_argument('title')
        description = self.get_argument('description')
        parsed_uuid = None

        try:
            points = round(float(self.get_argument('points')))
        except ValueError:
            points = 0

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


class MostCommonViolationsHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        violations = yield Violation.get_most_common_violations()

        result = []
        for name, count in violations.items():
            result.append({'name': name, 'count': count})

        self.write_json(result)
        self.finish()
