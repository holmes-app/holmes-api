#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect
from tornado.testing import gen_test

from holmes.models.review import Review
from tests.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class TestViolations(ApiTestCase):
    @gen_test
    def test_can_create_violation(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        review.add_violation(key="some.random.fact", title="test title", description="test description", points=1203)
        yield review.save()

        loaded_review = yield Review.objects.get(review._id)

        expect(loaded_review.violations).to_length(1)
        expect(loaded_review.violations[0].key).to_equal("some.random.fact")
        expect(loaded_review.violations[0].title).to_equal("test title")
        expect(loaded_review.violations[0].description).to_equal("test description")
        expect(loaded_review.violations[0].points).to_equal(1203)
