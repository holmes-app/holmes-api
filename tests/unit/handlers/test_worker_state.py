#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError

from holmes.models import Worker, Page, Review
from tests.unit.base import ApiTestCase
from tests.fixtures import WorkerFactory, ReviewFactory


class TestWorkerStateHandler(ApiTestCase):

    @gen_test
    def test_worker_start_working(self):
        review = ReviewFactory.create()
        worker = WorkerFactory.create()
        self.db.flush()

        response = yield self.http_client.fetch(
            self.get_url('/worker/%s/review/%s/start' % (str(worker.uuid), str(review.uuid))),
            method='POST',
            body=''
        )

        worker = Worker.by_uuid(worker.uuid, self.db)

        expect(worker).not_to_be_null()
        expect(response.code).to_equal(200)
        expect(response.body).to_be_like('OK')
        expect(str(worker.current_review)).to_equal(str(review.uuid))

    @gen_test
    def test_worker_start_working_invalid_worker(self):
        try:
            yield self.http_client.fetch(
                self.get_url('/worker/%s/review/%s/start' % (self.ZERO_UUID, self.ZERO_UUID)),
                method='POST',
                body=''
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like('Unknown Worker')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_worker_start_working_invalid_review(self):
        worker = WorkerFactory.create()
        self.db.flush()

        try:
            yield self.http_client.fetch(
                self.get_url('/worker/%s/review/%s/start' % (str(worker.uuid), self.ZERO_UUID)),
                method='POST',
                body=''
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like('Unknown Review')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_worker_start_working_already_complete_review(self):
        review = ReviewFactory.create(is_complete=True)
        worker = WorkerFactory.create()

        self.db.flush()

        try:
            yield self.http_client.fetch(
                self.get_url('/worker/%s/review/%s/start' % (str(worker.uuid), str(review.uuid))),
                method='POST',
                body=''
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(400)
            expect(err.response.reason).to_be_like('Review already completed')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_worker_complete_work(self):
        review = ReviewFactory.create()
        worker = WorkerFactory.create(current_review=review)
        self.db.flush()

        response = yield self.http_client.fetch(
            self.get_url('/worker/%s/review/%s/complete' % (str(worker.uuid), str(review.uuid))),
            method='POST',
            body=''
        )

        worker = Worker.by_uuid(worker.uuid, self.db)
        page = Page.by_uuid(review.page.uuid, self.db)
        review = Review.by_uuid(review.uuid, self.db)

        expect(worker).not_to_be_null()
        expect(response.code).to_equal(200)
        expect(response.body).to_be_like('OK')
        expect(worker.current_review).to_be_null()

        expect(page.last_review.id).to_equal(review.id)

    @gen_test
    def test_worker_complete_work_invalid_worker(self):
        try:
            yield self.http_client.fetch(
                self.get_url('/worker/%s/review/%s/complete' % (self.ZERO_UUID, self.ZERO_UUID)),
                method='POST',
                body=''
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like('Unknown Worker')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_worker_complete_work_invalid_review(self):
        worker = WorkerFactory.create()
        self.db.flush()

        try:
            yield self.http_client.fetch(
                self.get_url('/worker/%s/review/%s/complete' % (str(worker.uuid), self.ZERO_UUID)),
                method='POST',
                body=''
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like('Unknown Review')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_can_complete_work_to_review_with_error(self):
        review = ReviewFactory.create()
        worker = WorkerFactory.create(current_review=review)
        self.db.flush()

        url = self.get_url(
            '/worker/%s/review/%s/complete' % (
                worker.uuid,
                review.uuid
            )
        )

        yield self.http_client.fetch(
            url,
            method='POST',
            body='{"error":"Invalid Url"}'
        )

        review = Review.by_uuid(review.uuid, self.db)
        expect(review).not_to_be_null()
        expect(review.failed).to_be_true()
        expect(review.failure_message).to_equal('Invalid Url')
