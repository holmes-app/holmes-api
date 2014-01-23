#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from uuid import UUID, uuid4

from tornado import gen
from ujson import loads, dumps

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
        if self._parse_uuid(review_uuid):
            review = Review.by_uuid(review_uuid, self.db)

        if not review:
            self.set_status(404, 'Review with uuid of %s not found!' % review_uuid)
            return

        result = review.to_dict(self.application.fact_definitions, self.application.violation_definitions)
        result.update({
            'violationPoints': review.get_violation_points(),
            'violationCount': review.violation_count,
        })

        self.write_json(result)


class LastReviewsHandler(BaseReviewHandler):
    def get(self):
        reviews = Review.get_last_reviews(self.db)

        reviews_json = []
        for review in reviews:
            review_dict = review.to_dict(self.application.fact_definitions, self.application.violation_definitions)
            data = {
                'violationCount': review.violation_count,
            }
            review_dict.update(data)
            reviews_json.append(review_dict)

        self.write_json(reviews_json)
