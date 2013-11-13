#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime

from preggy import expect
from tornado.testing import gen_test
from ujson import loads

from holmes.models import Review
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class TestNextJobHandler(ApiTestCase):
    @gen_test
    def test_can_get_next_job_returns_empty_string_if_none_available(self):
        response = yield self.http_client.fetch(
            self.get_url('/next'),
            method='POST',
            body=''
        )

        expect(response.code).to_equal(200)
        expect(response.body).to_be_empty()

    @gen_test
    def test_can_get_next_job_to_new_pages(self):
        page = PageFactory.create()

        response = yield self.http_client.fetch(
            self.get_url('/next'),
            method='POST',
            body=''
        )

        expect(response.code).to_equal(200)
        expect(response.body).not_to_be_empty()

        next_job = loads(response.body)
        expect(next_job['page']).not_to_be_null()
        expect(next_job['page']).to_equal(str(page.uuid))

    @gen_test
    def test_can_get_next_job(self):
        dt = datetime(2010, 10, 10, 10, 10, 10)

        page = PageFactory.create()
        review = ReviewFactory.create(page=page, is_complete=True, completed_date=dt)

        page.last_review = review
        page.last_review_date = dt
        self.db.flush()

        page2 = PageFactory.create(domain=page.domain)
        review2 = ReviewFactory.create(page=page2, is_complete=True, completed_date=datetime.now())

        page2.last_review = review2
        page2.last_review_date = review2.completed_date
        self.db.flush()

        response = yield self.http_client.fetch(
            self.get_url('/next'),
            method='POST',
            body=''
        )

        expect(response.code).to_equal(200)

        result = loads(response.body)

        expect(result['url']).to_equal(page.url)
        expect(result['page']).to_equal(str(page.uuid))

        loaded_review = Review.by_uuid(result['review'], self.db)

        expect(loaded_review).not_to_be_null()
        expect(loaded_review.page.uuid).to_equal(page.uuid)

    @gen_test
    def test_call_next_job_two_times_will_give_two_different_random_pages(self):
        domain = DomainFactory.create()

        page_one = PageFactory.create(domain=domain)
        page_two = PageFactory.create(domain=domain)

        expect(str(page_one.uuid)).not_to_equal(str(page_two.uuid))

        response = yield self.http_client.fetch(
            self.get_url('/next'),
            method='POST',
            body=''
        )
        expect(response.code).to_equal(200)
        expect(response.body).not_to_be_empty()
        first_request_page = loads(response.body)['page']

        response = yield self.http_client.fetch(
            self.get_url('/next'),
            method='POST',
            body=''
        )
        expect(response.code).to_equal(200)
        expect(response.body).not_to_be_empty()
        second_request_page = loads(response.body)['page']

        expect(second_request_page).not_to_equal(first_request_page)
