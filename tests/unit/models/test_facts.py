#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect
from tornado.testing import gen_test

from holmes.models.review import Review
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class TestFacts(ApiTestCase):
    @gen_test
    def test_can_create_facts(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        review.add_fact(key="some.random.fact", value=1203, unit="kb")
        yield review.save()

        loaded_review = yield Review.objects.get(review._id)

        expect(loaded_review.facts).to_length(1)
        expect(loaded_review.facts[0].key).to_equal("some.random.fact")
        expect(loaded_review.facts[0].value).to_equal(1203)
        expect(loaded_review.facts[0].unit).to_equal("kb")
