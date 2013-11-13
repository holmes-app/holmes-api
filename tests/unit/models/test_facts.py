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

    def test_fact_str_kb(self):
        fact = FactFactory.create(key="some.random.fact", value=1203, title="title", unit="kb")
        self.db.flush()

        loaded_fact = self.db.query(Fact).get(fact.id)

        expect(str(loaded_fact)).to_be_like('some.random.fact: 1203.00kb')

    def test_fact_str(self):
        fact = FactFactory.create(key="some.random.fact", value=1203, title="title", unit="kms")
        self.db.flush()

        loaded_fact = self.db.query(Fact).get(fact.id)

        expect(str(loaded_fact)).to_be_like('some.random.fact: 1203kms')
