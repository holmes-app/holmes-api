#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect
#from tornado.testing import gen_test

from holmes.models import Fact
from tests.unit.base import ApiTestCase
from tests.fixtures import FactFactory


class TestFacts(ApiTestCase):
    def test_can_create_facts(self):
        fact = FactFactory.create(value="whatever")
        self.db.flush()

        loaded_fact = self.db.query(Fact).get(fact.id)

        expect(loaded_fact.key).to_equal(fact.key)
        expect(loaded_fact.value).to_equal(fact.value)
        expect(loaded_fact.unit).to_equal(fact.unit)
        expect(loaded_fact.title).to_equal(fact.title)

    #@gen_test
    #def test_fact_str_kb(self):
        #domain = yield DomainFactory.create()
        #page = yield PageFactory.create(domain=domain)
        #review = yield ReviewFactory.create(page=page)

        #review.add_fact(key="some.random.fact", value=1203, title="title", unit="kb")
        #yield review.save()

        #loaded_review = yield Review.objects.get(review._id)

        #expect(loaded_review.facts).to_length(1)
        #expect(str(loaded_review.facts[0])).to_be_like('some.random.fact: 1203.00kb')

    #@gen_test
    #def test_fact_str(self):
        #domain = yield DomainFactory.create()
        #page = yield PageFactory.create(domain=domain)
        #review = yield ReviewFactory.create(page=page)

        #review.add_fact(key="some.random.fact", value=1203, title="title", unit="kms")
        #yield review.save()

        #loaded_review = yield Review.objects.get(review._id)

        #expect(loaded_review.facts).to_length(1)
        #expect(str(loaded_review.facts[0])).to_be_like('some.random.fact: 1203kms')
