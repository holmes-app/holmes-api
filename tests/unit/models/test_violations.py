#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect

from holmes.models import Violation, Key
from tests.unit.base import ApiTestCase
from tests.fixtures import ViolationFactory


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

    def test_can_get_most_common_violations(self):
        self.db.query(Violation).delete()

        for i in range(3):
            for j in range(2):
                ViolationFactory.create(
                    key=Key(name='some.random.fact.%s' % i),
                    value='value',
                    points=1203
                )

        violation_definitions = {
            'some.random.fact.0': {},
            'some.random.fact.1': {}
        }

        violations = Violation.get_most_common_violations(
            self.db,
            violation_definitions,
            limit=2
        )

        expect(violations).to_be_like([
            {
                'count': 1,
                'key': 'some.random.fact.0',
                'title': 'undefined'
            },
            {
                'count': 1,
                'key': 'some.random.fact.1',
                'title': 'undefined'
            }
        ])
