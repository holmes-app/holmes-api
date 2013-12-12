#!/usr/bin/python
# -*- coding: utf-8 -*-

from ujson import loads
from tests.unit.base import ApiTestCase
from preggy import expect
from tornado.testing import gen_test

from tests.fixtures import ReviewFactory
from holmes.models import Key


class TestMostCommonViolationsHandler(ApiTestCase):
    @gen_test
    def test_can_get_most_common_violations(self):
        review = ReviewFactory.create()

        for i in range(5):
            key = Key.get_or_create(self.db, 'violation1')
            review.add_violation(key, 'value', 100)

        for j in range(2):
            key = Key.get_or_create(self.db, 'violation2')
            review.add_violation(key, 'value', 300)

        self.db.flush()

        response = yield self.http_client.fetch(
            self.get_url('/most-common-violations/')
        )

        violations = loads(response.body)

        expect(response.code).to_equal(200)

        expect(violations).to_be_like([
            {u'count': 5, u'name': u'undefined'},
            {u'count': 2, u'name': u'undefined'}
        ])
