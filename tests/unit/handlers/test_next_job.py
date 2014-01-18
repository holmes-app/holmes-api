#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime

from preggy import expect
from tornado.testing import gen_test
from ujson import loads

from holmes.models import Domain, Page
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class TestNextJobHandler(ApiTestCase):
    @gen_test
    def test_can_get_next_job_returns_empty_string_if_none_available(self):
        response = yield self.http_client.fetch(
            self.get_url('/next'),
        )

        expect(response.code).to_equal(200)
        expect(response.body).to_be_empty()

    @gen_test
    def test_can_get_next_job_to_new_pages(self):
        page = PageFactory.create()

        response = yield self.http_client.fetch(
            self.get_url('/next'),
        )

        expect(response.code).to_equal(200)
        expect(response.body).not_to_be_empty()

        next_job = loads(response.body)
        expect(next_job['page']).not_to_be_null()
        expect(next_job['page']).to_equal(str(page.uuid))

    @gen_test
    def test_can_get_next_job(self):
        page = PageFactory.create()
        ReviewFactory.create(page=page)
        self.db.flush()

        page2 = PageFactory.create(domain=page.domain)
        review2 = ReviewFactory.create(page=page2, is_complete=True, completed_date=datetime.now())

        page2.last_review = review2
        page2.last_review_date = review2.completed_date
        self.db.flush()

        response = yield self.http_client.fetch(
            self.get_url('/next'),
        )

        expect(response.code).to_equal(200)

        result = loads(response.body)

        expect(result['url']).to_equal(page.url)
        expect(result['page']).to_equal(str(page.uuid))

    @gen_test
    def test_call_next_job_two_times_will_give_two_different_random_pages(self):
        domain = DomainFactory.create()

        for i in range(100):
            PageFactory.create(domain=domain)

        response = yield self.http_client.fetch(
            self.get_url('/next'),
        )
        expect(response.code).to_equal(200)
        expect(response.body).not_to_be_empty()
        first_request_page = loads(response.body)['page']

        response = yield self.http_client.fetch(
            self.get_url('/next'),
        )
        expect(response.code).to_equal(200)
        expect(response.body).not_to_be_empty()
        second_request_page = loads(response.body)['page']

        expect(second_request_page).not_to_equal(first_request_page)

    @gen_test
    def test_call_next_job_will_return_a_active_domain(self):
        self.db.query(Domain).delete()

        active_domain = DomainFactory.create()
        inactive_domain = DomainFactory.create(is_active=False)

        for i in range(10):
            PageFactory.create(domain=active_domain)

        for i in range(10):
            PageFactory.create(domain=inactive_domain)

        response = yield self.http_client.fetch(
            self.get_url('/next'),
        )
        expect(response.code).to_equal(200)
        expect(response.body).not_to_be_empty()
        requested_page = loads(response.body)['page']

        page = self.db.query(Page).filter(Page.uuid == requested_page).one()
        expect(page.domain).not_to_equal(inactive_domain)
