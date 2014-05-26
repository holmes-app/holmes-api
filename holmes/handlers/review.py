#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
from uuid import UUID

from holmes.models import Review, Page
from holmes.handlers import BaseHandler


class BaseReviewHandler(BaseHandler):
    def _parse_uuid(self, uuid):
        try:
            return UUID(uuid)
        except ValueError:
            return None


class ReviewHandler(BaseReviewHandler):
    def get(self, page_uuid, review_uuid):
        review = None
        page = None
        if self._parse_uuid(review_uuid):
            review = Review.by_uuid(review_uuid, self.db)

        if self._parse_uuid(page_uuid):
            page = Page.by_uuid(page_uuid, self.db)

        if not review and page:
            self.redirect('/page/%s/review/%s/' % (page_uuid, page.last_review_uuid))
            return

        if not page:
            self.set_status(404, self._('Page UUID [%s] not found') % page_uuid)
            return

        result = review.to_dict(self.application.fact_definitions, self.application.violation_definitions)
        result.update({
            'violationPoints': review.get_violation_points(),
            'violationCount': review.violation_count,
        })

        self.write_json(result)


class LastReviewsHandler(BaseReviewHandler):
    def get(self):
        reviews = Review.get_last_reviews(
            self.db, domain_filter=self.get_argument('domain_filter', None)
        )

        reviews_json = []
        for review in reviews:
            review_dict = review.to_dict(self.application.fact_definitions, self.application.violation_definitions)
            data = {
                'violationCount': review.violation_count,
            }
            review_dict.update(data)
            reviews_json.append(review_dict)

        self.write_json(reviews_json)


class ReviewsInLastHourHandler(BaseReviewHandler):
    def get(self):
        from_date = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        count, first_date = Review.get_reviews_count_in_period(
            self.db,
            from_date=from_date,
            domain_filter=self.get_argument('domain_filter', None)
        )

        if first_date:
            ellapsed = (datetime.datetime.utcnow() - first_date).total_seconds()
        else:
            ellapsed = 3600

        self.write_json({'count': count, 'ellapsed': ellapsed})
