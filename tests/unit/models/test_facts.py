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

        review.add_fact(key="some.random.fact", value=1203, title="title", unit="kb")
        yield review.save()

        loaded_review = yield Review.objects.get(review._id)

        expect(loaded_review.facts).to_length(1)
        expect(loaded_review.facts[0].key).to_equal("some.random.fact")
        expect(loaded_review.facts[0].value).to_equal(1203)
        expect(loaded_review.facts[0].unit).to_equal("kb")
        expect(loaded_review.facts[0].title).to_equal("title")

    @gen_test
    def test_can_create_facts_float(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        review.add_fact(key="some.random.fact", value=1203.01, title="title", unit="kb")
        yield review.save()

        loaded_review = yield Review.objects.get(review._id)

        expect(loaded_review.facts).to_length(1)
        expect(loaded_review.facts[0].key).to_equal("some.random.fact")
        expect(loaded_review.facts[0].value).to_equal(1203.01)
        expect(loaded_review.facts[0].unit).to_equal("kb")
        expect(loaded_review.facts[0].title).to_equal("title")

    @gen_test
    def test_fact_str_kb(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        review.add_fact(key="some.random.fact", value=1203, title="title", unit="kb")
        yield review.save()

        loaded_review = yield Review.objects.get(review._id)

        expect(loaded_review.facts).to_length(1)
        expect(str(loaded_review.facts[0])).to_be_like('some.random.fact: 1203.00kb')

    @gen_test
    def test_fact_str(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        review.add_fact(key="some.random.fact", value=1203, title="title", unit="kms")
        yield review.save()

        loaded_review = yield Review.objects.get(review._id)

        expect(loaded_review.facts).to_length(1)
        expect(str(loaded_review.facts[0])).to_be_like('some.random.fact: 1203kms')
