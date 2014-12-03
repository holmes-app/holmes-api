#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect

from holmes.models import Violation, Key
from holmes.utils import _
from tests.unit.base import ApiTestCase
from tests.fixtures import ViolationFactory, KeyFactory, DomainFactory


class TestViolations(ApiTestCase):
    def test_can_create_violation(self):
        violation = ViolationFactory.create(
            key=Key(name='some.random.fact'), value='value', points=1203
        )

        loaded_violation = self.db.query(Violation).get(violation.id)

        expect(loaded_violation.value).to_equal('value')
        expect(loaded_violation.key.name).to_equal('some.random.fact')
        expect(loaded_violation.points).to_equal(1203)
        expect(str(loaded_violation)).to_be_like('%s: %s' % (
            violation.key.name,
            violation.value,
        ))

    def test_to_dict(self):
        violation = ViolationFactory.create(
            key=Key(name='some.random.fact'),
            value='value',
            points=1203,
        )

        violations_definitions = {'some.random.fact': {}}

        expect(violation.to_dict(violations_definitions, _)).to_be_like({
            'key': 'some.random.fact',
            'description': 'value',
            'title': 'undefined',
            'points': 1203,
            'category': 'undefined'
        })

    def test_to_dict_with_violations_definitions_params(self):
        violation1 = ViolationFactory.create(
            key=Key(name='some.random.fact.1'),
            value='value',
            points=120,
        )

        violation2 = ViolationFactory.create(
            key=Key(name='some.random.fact.2'),
            value='violations',
            points=500,
        )

        violation3 = ViolationFactory.create(
            key=Key(name='some.random.fact.3'),
            value={'page_url': 'http://globo.com'},
            points=300,
        )

        violation4 = ViolationFactory.create(
            key=Key(name='some.random.fact.4'),
            value=None,
            points=100,
        )

        violations_definitions = {
            'some.random.fact.1': {'description': 'test'},
            'some.random.fact.2': {'description': 'test for: %s'},
            'some.random.fact.3': {'description': 'url: %(page_url)s'},
            'some.random.fact.4': {'description': 'my description'},
        }

        expect(violation1.to_dict(violations_definitions, _)).to_be_like({
            'key': 'some.random.fact.1',
            'description': 'test',
            'title': 'undefined',
            'points': 120,
            'category': 'undefined'
        })

        expect(violation2.to_dict(violations_definitions, _)).to_be_like({
            'key': 'some.random.fact.2',
            'description': 'test for: violations',
            'title': 'undefined',
            'points': 500,
            'category': 'undefined'
        })

        expect(violation3.to_dict(violations_definitions, _)).to_be_like({
            'key': 'some.random.fact.3',
            'description': 'url: http://globo.com',
            'title': 'undefined',
            'points': 300,
            'category': 'undefined'
        })

        expect(violation4.to_dict(violations_definitions, _)).to_be_like({
            'key': 'some.random.fact.4',
            'description': 'my description',
            'title': 'undefined',
            'points': 100,
            'category': 'undefined'
        })


    def test_can_get_most_common_violations_names(self):
        for i in range(3):
            key = KeyFactory.create(name='some.random.fact.%s' % i)
            for j in range(i):
                ViolationFactory.create(key=key)

        violations = Violation.get_most_common_violations_names(self.db)

        expect(violations).to_be_like([('some.random.fact.1', 1), ('some.random.fact.2', 2)])

    def test_get_group_by_key_id_for_all_domains(self):
        domains = [DomainFactory.create(name='g%d.com' % i) for i in range(2)]
        keys = [KeyFactory.create(name='random.fact.%s' % i) for i in range(3)]

        for i in range(3):
            for j in range(i + 1):
                ViolationFactory.create(
                    key=keys[i],
                    domain=domains[j % 2]
                )

        violations = Violation.get_group_by_key_id_for_all_domains(self.db)

        expect(violations).to_length(5)
        expect(violations[0]).to_be_like((keys[2].id, 'g0.com', 2))

    def test_can_get_group_by_value_for_key(self):
        self.db.query(Key).delete()
        self.db.query(Violation).delete()
        keys = [KeyFactory.create(name='random.key.%s' % i) for i in range(3)]

        for i in range(3):
            for j in range(i + 1):
                ViolationFactory.create(
                    key=keys[i],
                    value='random.value.%d' % i
                )

        violations = Violation.get_group_by_value_for_key(self.db, keys[0].name)
        expect(violations).to_be_like([('random.value.0', 1)])

        violations = Violation.get_group_by_value_for_key(self.db, keys[1].name)
        expect(violations).to_be_like([('random.value.1', 2)])

        violations = Violation.get_group_by_value_for_key(self.db, keys[2].name)
        expect(violations).to_be_like([('random.value.2', 3)])

    def test_can_get_top_in_category_for_all_domains(self):
        domains = [DomainFactory.create(name='g%d.com' % i) for i in range(2)]
        keys = [KeyFactory.create(name='random.fact.%s' % i) for i in range(3)]

        for i in range(3):
            for j in range(i + 1):
                ViolationFactory.create(
                    key=keys[i],
                    domain=domains[j % 2]
                )
        violations = Violation.get_top_in_category_for_all_domains(self.db)

        expect(violations).to_length(5)
        top = ('g0.com', keys[2].category_id, str(keys[2]), 2)
        expect(violations[0]).to_be_like(top)
