#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from ujson import loads

from preggy import expect
from tornado.testing import gen_test

from tests.unit.base import ApiTestCase
from tests.fixtures import PageFactory, ReviewFactory


class TestSearchHandler(ApiTestCase):

    @gen_test
    def test_can_search(self):
        dt = datetime.now()

        page = PageFactory.create(url="http://www.globo.com")

        review1 = ReviewFactory.create(
            page=page, is_active=True, is_complete=True,
            completed_date=dt, number_of_violations=20
        )
        self.db.flush()

        page.last_review = review1
        page.last_review_date = dt
        self.db.flush()

        response = yield self.http_client.fetch(
            self.get_url('/search?term=http://www.globo.com'),
            method='GET',
        )

        expect(response.code).to_equal(200)

        obj = loads(response.body)

        expect(obj).to_length(1)
