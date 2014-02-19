#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect

from holmes.models import Violation, Key
from tests.unit.base import ApiTestCase
from tests.fixtures import ViolationFactory, KeyFactory, KeysCategoryFactory


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
            points=1203
        )

        violations_definitions = {'some.random.fact': {}}

        expect(violation.to_dict(violations_definitions)).to_be_like({
            'key': 'some.random.fact',
            'description': 'value',
            'title': 'undefined',
            'points': 1203
        })

    def test_can_get_most_common_violations(self):
        self.db.query(Violation).delete()
        self.db.query(Key).delete()

        category = KeysCategoryFactory.create(name='SEO')
        for i in range(3):
            key = KeyFactory.create(name='some.random.fact.%s' % i, category=category)
            for j in range(i):
                ViolationFactory.create(
                    key=key,
                    value='value',
                    points=10 * i + j
                )

        violation_definitions = {
            'some.random.fact.1': {
                'title': 'SEO',
                'category': 'SEO'
            },
            'some.random.fact.2': {
                'title': 'SEO',
                'category': 'SEO'
            }
        }

        violations = Violation.get_most_common_violations(
            self.db,
            violation_definitions
        )

        expect(violations).to_be_like([
            {
                'count': 1,
                'key': 'some.random.fact.1',
                'category': 'SEO',
                'title': 'SEO'
            },
            {
                'count': 2,
                'key': 'some.random.fact.2',
                'category': 'SEO',
                'title': 'SEO'
            }
        ])

        violations = Violation.get_most_common_violations(
            self.db,
            violation_definitions,
            limit=2
        )

        expect(violations).to_be_like([
            {
                'count': 2,
                'key': 'some.random.fact.2',
                'category': 'SEO',
                'title': 'SEO'
            }
        ])
