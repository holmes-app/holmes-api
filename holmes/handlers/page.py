#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import UUID

from holmes.models import Page, Review
from holmes.handlers import BaseHandler


class PageHandler(BaseHandler):
    def get(self, uuid=''):
        uuid = UUID(uuid)

        page = Page.by_uuid(uuid, self.db)

        if not page:
            self.set_status(404, 'Page UUID [%s] not found' % uuid)
            return

        page_json = {
            "uuid": str(page.uuid),
            "url": page.url
        }

        self.write(page_json)


class PageReviewsHandler(BaseHandler):

    def get(self, uuid='', limit=10):
        uuid = UUID(uuid)

        page = Page.by_uuid(uuid, self.db)

        if not page:
            self.set_status(404, 'Page UUID [%s] not found' % uuid)
            return

        reviews = self.db.query(Review) \
            .filter(Review.page == page) \
            .filter(Review.is_complete == True) \
            .order_by(Review.completed_date.desc())[:limit]

        result = []
        for review in reviews:
            result.append({
                'uuid': str(review.uuid),
                'completedAt': review.completed_date,
                'violationCount': review.violation_count
            })

        self.write_json(result)


class PageViolationsPerDayHandler(BaseHandler):

    def get(self, uuid):
        page = Page.by_uuid(uuid, self.db)

        if not page:
            self.set_status(404, 'Page UUID [%s] not found' % uuid)
            return

        violations_per_day = page.get_violations_per_day(self.db)

        page_json = {
            "violations": violations_per_day
        }

        self.write_json(page_json)
