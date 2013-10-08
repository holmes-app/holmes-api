#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError

from holmes.models import Worker, Page, Review
from tests.unit.base import ApiTestCase
from tests.fixtures import WorkerFactory, DomainFactory, PageFactory, ReviewFactory


class TestWorkerStateHandler(ApiTestCase):
    zero_uuid = "00000000-0000-0000-0000-000000000000"

    @gen_test
    def test_worker_start_working(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

        review = yield ReviewFactory.create(page=page)
        worker = yield WorkerFactory.create()

        response = yield self.http_client.fetch(
            self.get_url('/worker/%s/start/%s' % (str(worker.uuid), str(review.uuid))),
            method='POST',
            body=''
        )

        worker = yield Worker.objects.get(uuid=worker.uuid)

        expect(worker).not_to_be_null()
        expect(response.code).to_equal(200)
        expect(response.body).to_be_like("OK")
        expect(str(worker.current_review)).to_equal(str(review.uuid))

    @gen_test
    def test_worker_start_working_invalid_worker(self):
        try:
            yield self.http_client.fetch(
                self.get_url('/worker/%s/start/%s' % (self.zero_uuid, self.zero_uuid)),
                method='POST',
                body=''
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like("Unknown Worker")
        else:
            assert False, "Should not have got this far"

    @gen_test
    def test_worker_start_working_invalid_review(self):

        worker = yield WorkerFactory.create()

        try:
            yield self.http_client.fetch(
                self.get_url('/worker/%s/start/%s' % (str(worker.uuid), self.zero_uuid)),
                method='POST',
                body=''
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like("Unknown Review")
        else:
            assert False, "Should not have got this far"

    @gen_test
    def test_worker_start_working_already_complete_review(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

        review = yield ReviewFactory.create(page=page, is_complete=True)
        worker = yield WorkerFactory.create()

        try:
            yield self.http_client.fetch(
                self.get_url('/worker/%s/start/%s' % (str(worker.uuid), str(review.uuid))),
                method='POST',
                body=''
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(400)
            expect(err.response.reason).to_be_like("Review already completed")
        else:
            assert False, "Should not have got this far"

    @gen_test
    def test_worker_complete_work(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

        review = yield ReviewFactory.create(page=page)
        worker = yield WorkerFactory.create(current_review=review)

        response = yield self.http_client.fetch(
            self.get_url('/worker/%s/complete/%s' % (str(worker.uuid), str(review.uuid))),
            method='POST',
            body=''
        )

        worker = yield Worker.objects.get(uuid=worker.uuid)
        page = yield Page.objects.get(uuid=page.uuid)
        page.load_references(['last_review'])
        review = yield Review.objects.get(uuid=review.uuid)

        expect(worker).not_to_be_null()
        expect(response.code).to_equal(200)
        expect(response.body).to_be_like('OK')
        expect(worker.current_review).to_be_null()

    @gen_test
    def test_worker_complete_work_invalid_worker(self):
        try:
            yield self.http_client.fetch(
                self.get_url('/worker/%s/complete/%s' % (self.zero_uuid, self.zero_uuid)),
                method='POST',
                body=''
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like("Unknown Worker")
        else:
            assert False, "Should not have got this far"

    @gen_test
    def test_worker_complete_work_invalid_review(self):

        worker = yield WorkerFactory.create()

        try:
            yield self.http_client.fetch(
                self.get_url('/worker/%s/complete/%s' % (str(worker.uuid), self.zero_uuid)),
                method='POST',
                body=''
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like("Unknown Review")
        else:
            assert False, "Should not have got this far"
