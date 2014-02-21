#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect
#from tornado.testing import gen_test

from holmes.models import Fact, Key
from tests.unit.base import ApiTestCase
from tests.fixtures import FactFactory


class TestFacts(ApiTestCase):
    def test_can_create_facts(self):
        fact = FactFactory.create(
            key=Key(name='some.random.fact'),
            value='whatever'
        )

        loaded_fact = self.db.query(Fact).get(fact.id)

        expect(loaded_fact.key.name).to_equal('some.random.fact')
        expect(loaded_fact.value).to_equal('whatever')

    def test_to_dict(self):
        fact = FactFactory.create(
            key=Key(name='some.random.fact'),
            value='whatever',
        )

        facts_definitions = {'some.random.fact': {}}

        expect(fact.to_dict(facts_definitions)).to_be_like({
            'key': 'some.random.fact',
            'value': 'whatever',
            'unit': 'value',
            'title': 'unknown',
            'category': 'unknown'
        })

    def test_fact_str(self):
        fact = FactFactory.create(
            key=Key(name="some.random.fact"),
            value=1203,
        )

        loaded_fact = self.db.query(Fact).get(fact.id)

        expect(str(loaded_fact)).to_be_like('some.random.fact: 1203')
