#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from uuid import uuid4
from datetime import datetime

from preggy import expect
#from tornado.testing import gen_test

from holmes.models import Review
from tests.unit.base import ApiTestCase
from tests.fixtures import ReviewFactory, PageFactory


class TestReview(ApiTestCase):
    def test_can_create_review(self):
        review = ReviewFactory.create()

        expect(review.id).not_to_be_null()
        expect(review.created_date).to_be_like(datetime.now())

        expect(review.page).not_to_be_null()
        expect(review.domain).not_to_be_null()

        loaded = self.db.query(Review).get(review.id)

        expect(loaded.created_date).to_be_like(review.created_date)
        expect(loaded.is_complete).to_be_like(review.is_complete)
        expect(loaded.uuid).not_to_be_null()

    def test_can_create_facts_float(self):
        review = ReviewFactory.create()

        review.add_fact(key="some.random.fact", value=1203.01, title="title", unit="kb")

        loaded_review = self.db.query(Review).get(review.id)

        expect(loaded_review.facts).to_length(1)
        expect(loaded_review.facts[0].key).to_equal("some.random.fact")
        expect(loaded_review.facts[0].value).to_equal(1203.01)
        expect(loaded_review.facts[0].unit).to_equal("kb")
        expect(loaded_review.facts[0].title).to_equal("title")

    def test_can_append_facts(self):
        review = ReviewFactory.build()
        expect(review.facts).to_length(0)

        review.add_fact('a', 'b', 'c', 'd')
        expect(review.facts).to_length(1)
        expect(review.facts[0].key).to_equal('a')
        expect(review.facts[0].value).to_equal('b')
        expect(review.facts[0].title).to_equal('c')
        expect(review.facts[0].unit).to_equal('d')

    def test_can_append_violations(self):
        review = ReviewFactory.build()
        expect(review.violations).to_length(0)

        review.add_violation('a', 'b', 'c', 100)
        expect(review.violations).to_length(1)
        expect(review.violations[0].key).to_equal('a')
        expect(review.violations[0].title).to_equal('b')
        expect(review.violations[0].description).to_equal('c')
        expect(review.violations[0].points).to_equal(100)

    def test_cant_append_facts_after_complete(self):
        review = ReviewFactory.build()
        expect(review.facts).to_length(0)
        review.is_complete = True

        try:
            review.add_fact('a', 'b', 'c', 'd')
        except ValueError:
            err = sys.exc_info()[1]
            expect(err).to_have_an_error_message_of("Can't add anything to a completed review.")
        else:
            assert False, 'Should not have gotten this far'

    def test_cant_append_violations_after_complete(self):
        review = ReviewFactory.build()
        expect(review.facts).to_length(0)
        review.is_complete = True

        try:
            review.add_violation('a', 'b', 'c', 10)
        except ValueError:
            err = sys.exc_info()[1]
            expect(err).to_have_an_error_message_of("Can't add anything to a completed review.")
        else:
            assert False, 'Should not have gotten this far'

    def test_review_has_failed(self):
        review = ReviewFactory.build()
        review.failure_message = "Invalid Page"
        expect(review.failed).to_be_true()

    def test_can_get_last_reviews(self):
        dt = datetime(2010, 10, 10, 10, 10, 10)
        dt2 = datetime(2010, 10, 11, 10, 10, 10)
        dt3 = datetime(2010, 10, 12, 10, 10, 10)

        review = ReviewFactory.create(is_active=True, is_complete=True, completed_date=dt3)
        review2 = ReviewFactory.create(is_active=True, is_complete=True, completed_date=dt2)
        ReviewFactory.create(is_active=True, is_complete=True, completed_date=dt)
        ReviewFactory.create(is_active=False, is_complete=True, completed_date=dt)
        ReviewFactory.create(is_active=False, is_complete=True, completed_date=dt)
        ReviewFactory.create(is_active=False, is_complete=True, completed_date=dt)
        ReviewFactory.create(is_active=False, is_complete=True, completed_date=dt)
        ReviewFactory.create(is_active=False, is_complete=True, completed_date=dt)

        last_reviews = Review.get_last_reviews(self.db, limit=2)
        expect(last_reviews).to_length(2)

        expect(last_reviews[0].id).to_equal(review.id)
        expect(last_reviews[1].id).to_equal(review2.id)

    def test_can_get_violation_points(self):
        review = ReviewFactory.create(number_of_violations=20)
        expect(review.get_violation_points()).to_equal(190)

    def test_can_get_review_by_uuid(self):
        review = ReviewFactory.create()

        loaded = Review.by_uuid(review.uuid, self.db)
        expect(loaded.id).to_equal(review.id)

        invalid = Review.by_uuid(uuid4(), self.db)
        expect(invalid).to_be_null()

    def test_to_dict(self):
        page_id = uuid4()
        review_id = uuid4()
        page = PageFactory.build(uuid=page_id)
        review = ReviewFactory.build(page=page, uuid=review_id)
        review.add_violation('a', 'b', 'c', 100)
        review.add_fact('a', 'b', 'c', 'd')

        expect(review.to_dict()).to_be_like({
            'domain': review.domain.name,
            'uuid': str(review_id),
            'completedAt': None,
            'facts': [
                {'value': 'b', 'unit': 'd', 'key': 'a', 'title': 'c'}
            ],
            'violations': [
                {'points': 100, 'description': 'c', 'key': 'a', 'title': 'b'}
            ],
            'page': {
                'url': page.url,
                'uuid': str(page_id)
            },
            'createdAt': None,
            'isComplete': False
        })
