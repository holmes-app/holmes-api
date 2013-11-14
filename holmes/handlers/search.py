#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado import gen

from holmes.models import Page
from holmes.handlers import BaseHandler


class SearchHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        term = self.get_argument('term')

        pages = self.db.query(Page) \
            .filter(Page.url.like('%%%s%%' % term)) \
            .filter(Page.last_review_date != None) \
            .all()

        pages_json = []

        for page in pages:
            pages_json.append({
                "uuid": str(page.uuid),
                "url": page.url,
                "reviewId": str(page.last_review.uuid)
            })

        self.write_json(pages_json)
        self.finish()
