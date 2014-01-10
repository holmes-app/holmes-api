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

    @gen.coroutine
    def post(self, page_uuid, review_uuid=None):
        page = Page.by_uuid(page_uuid, self.db)

        review_data = loads(self.get_argument('review'))

        page.expires = review_data['expires']
        if page.expires is not None:
            page.expires = datetime.utcfromtimestamp(page.expires)

        page.last_modified = review_data['lastModified']
        if page.last_modified is not None:
            page.last_modified = datetime.utcfromtimestamp(page.last_modified)

        self.db.flush()

        review = Review(
            domain=page.domain,
            page=page,
            is_active=True,
            is_complete=False,
            completed_date=datetime.utcnow(),
            uuid=uuid4(),
        )

        self.db.add(review)
        self.db.flush()

        for fact in review_data['facts']:
            name = fact['key']
            key = self.application.fact_definitions[name]['key']
            review.add_fact(key, fact['value'])

        self.db.flush()

        for violation in review_data['violations']:
            name = violation['key']
            key = self.application.violation_definitions[name]['key']
            review.add_violation(key, violation['value'], violation['points'])

        self.db.flush()

        page.violations_count = len(review_data['violations'])
        self.db.flush()

        review.is_complete = True
        self.db.flush()

        if not page.last_review:
            yield self.cache.increment_active_review_count(page.domain)

            yield self.cache.increment_violations_count(
                page.domain,
                increment=page.violations_count
            )
        else:
            old_violations_count = len(page.last_review.violations)
            new_violations_count = len(review.violations)

            yield self.cache.increment_violations_count(
                page.domain,
                increment=new_violations_count - old_violations_count
            )

            page.last_review.is_active = False
            self.db.flush()

        page.last_review_uuid = review.uuid
        page.last_review = review
        self.db.flush()

        page.last_review_date = review.completed_date
        self.db.flush()

        self._remove_older_reviews_with_same_day(review)

        self.application.event_bus.publish(dumps({
            'type': 'new-review',
            'reviewId': str(review.uuid)
        }))

    def _remove_older_reviews_with_same_day(self, review):
        dt = datetime.now()
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)

        for review in self.db.query(Review) \
                .filter(Review.page == review.page) \
                .filter(Review.uuid != review.uuid) \
                .filter(Review.created_date >= dt) \
                .all():

            for fact in review.facts:
                self.db.delete(fact)

            self.db.flush()

            for violation in review.violations:
                self.db.delete(violation)

            self.db.flush()

            self.db.delete(review)

            self.db.flush()


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
