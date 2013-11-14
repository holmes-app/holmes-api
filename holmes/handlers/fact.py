#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import UUID
from ujson import loads

from tornado import gen

from holmes.models import Review
from holmes.handlers import BaseHandler


class CreateFactHandler(BaseHandler):

    @gen.coroutine
    def post(self, page_uuid, review_uuid):
        key = self.get_argument('key')
        unit = self.get_argument('unit', None)
        value = self.get_argument('value')
        title = self.get_argument('title')

        parsed_uuid = None
        try:
            parsed_uuid = UUID(review_uuid)
        except ValueError:
            pass

        review = None
        if parsed_uuid:
            review = Review.by_uuid(parsed_uuid, self.db)

        if not review:
            self.set_status(404, 'Review with uuid of %s not found!' % review_uuid)
            self.finish()
            return

        review.add_fact(key=key, unit=unit, value=value, title=title)
        self.db.flush()

        self.write('OK')
        self.finish()
