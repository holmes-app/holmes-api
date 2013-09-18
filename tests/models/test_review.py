#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime

from preggy import expect
from tornado.testing import gen_test

from tests.base import ApiTestCase
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

    def test_can_append_facts(self):
        review = ReviewFactory.build()
        expect(review.facts).to_length(0)

        review.add_fact("a", "b", "c")
        expect(review.facts).to_length(1)
        expect(review.facts[0].key).to_equal("a")
        expect(review.facts[0].value).to_equal("b")
        expect(review.facts[0].unit).to_equal("c")
