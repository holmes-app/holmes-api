#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect

from holmes.models import Violation
from tests.unit.base import ApiTestCase
from tests.fixtures import ViolationFactory


class TestViolations(ApiTestCase):
    def test_can_create_violation(self):
        violation = ViolationFactory.create(
            key='some.random.fact', title='test title', description='test description', points=1203
        )

        loaded_violation = self.db.query(Violation).get(violation.id)

        expect(loaded_violation.title).to_equal('test title')
        expect(loaded_violation.key).to_equal('some.random.fact')
        expect(loaded_violation.description).to_equal('test description')
        expect(loaded_violation.points).to_equal(1203)
        expect(str(loaded_violation)).to_be_like('%s: %s (%d points)\n%s' % (
            violation.key,
            violation.title,
            violation.points,
            violation.description
        ))

    def test_can_get_most_common_violations(self):
        self.db.query(Violation).delete()

        for i in range(3):
            for j in range(2):
                ViolationFactory.create(
                    key='some.random.fact.%s' % i, title='test title', description='test description', points=1203
                )

        expect(Violation.get_most_common_violations(self.db, limit=2)).to_be_like([
            {
                'title': u'test title',
                'count': 2,
                'key': 'some.random.fact.0'
            },
            {
                'title': u'test title',
                'count': 2,
                'key': 'some.random.fact.1'
            }
        ])
