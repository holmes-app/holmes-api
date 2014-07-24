#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy import or_

from holmes.models import Page
from holmes.handlers import BaseHandler
from holmes.utils import get_domain_from_url


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

        domain_name, domain_url = get_domain_from_url(page.url)

        self.write_json({
            "uuid": str(page.uuid),
            "url": page.url,
            "reviewId": str(page.last_review.uuid),
            "domain": domain_name
        })
