#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from datetime import datetime

from preggy import expect
from tornado.testing import gen_test

from holmes.models import Review
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class TestReview(ApiTestCase):
    @gen_test
    def test_can_create_review(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        expect(review._id).not_to_be_null()
        expect(review.created_date).to_be_like(datetime.now())

        expect(review.page._id).to_equal(page._id)

        loaded = yield Review.objects.get(review._id)
        expect(loaded.created_date).to_be_like(review.created_date)
        expect(loaded.is_complete).to_be_like(review.is_complete)
        expect(loaded.uuid).not_to_be_null()

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

    def test_review_has_falied(self):
        review = ReviewFactory.build()
        review.failure_message = "Invalid Page"
        expect(review.failed).to_be_true()

