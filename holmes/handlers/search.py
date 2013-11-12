#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado import gen

from holmes.models import Page
from holmes.handlers import BaseHandler


class SearchHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        term = self.get_argument('term')

        pages = yield Page.objects.filter(url=term, last_review_date__is_null=False).find_all()

        pages_json = []

        for page in pages:
            yield page.load_references(['last_review'])

            pages_json.append({
                "uuid": str(page.uuid),
                "title": page.title,
                "url": page.url,
                "reviewId": str(page.last_review.uuid)
            })

        self.write_json(pages_json)
        self.finish()
