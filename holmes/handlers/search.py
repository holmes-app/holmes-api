#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy import or_

from holmes.models import Page
from holmes.handlers import BaseHandler


class SearchHandler(BaseHandler):

    def get(self):
        term = self.get_argument('term')

        page = self.db.query(Page) \
            .filter(or_(
                Page.url == term,
                Page.url == term.rstrip('/')
            )) \
            .filter(Page.last_review != None) \
            .first()

        if page is None:
            self.write_json(None)
            return

        self.write_json({
            "uuid": str(page.uuid),
            "url": page.url,
            "reviewId": str(page.last_review.uuid)
        })
