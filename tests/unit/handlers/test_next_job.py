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
            body=""
        )

        expect(response.code).to_equal(200)
        expect(response.body).to_be_empty()

    @gen_test
    def test_can_get_next_job_to_new_pages(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

        response = yield self.http_client.fetch(
            self.get_url('/next'),
            method='POST',
            body=""
        )

        expect(response.code).to_equal(200)
        expect(response.body).not_to_be_empty()
        expect(loads(response.body)['page']).not_to_be_null()
        expect(loads(response.body)['page']).to_equal(str(page.uuid))

    @gen_test
    def test_can_get_next_job(self):
        dt = datetime(2010, 10, 10, 10, 10, 10)

        domain = yield DomainFactory.create()

        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page, is_complete=True, completed_date=dt)

        page.last_review = review
        page.last_review_date = dt
        yield page.save()

        page2 = yield PageFactory.create(domain=domain)
        review2 = yield ReviewFactory.create(page=page2, is_complete=True, completed_date=datetime.now())
        page2.last_review = review2
        page2.last_review_date = review2.completed_date
        yield page2.save()

        response = yield self.http_client.fetch(
            self.get_url('/next'),
            method='POST',
            body=""
        )

        expect(response.code).to_equal(200)

        result = loads(response.body)

        expect(result['url']).to_equal(page.url)
        expect(result['page']).to_equal(str(page.uuid))

        loaded_review = yield Review.objects.get(uuid=result['review'])
        yield loaded_review.load_references(['page'])

        expect(loaded_review).not_to_be_null()
        expect(loaded_review.page.uuid).to_equal(page.uuid)
