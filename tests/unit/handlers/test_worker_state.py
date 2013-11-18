#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError

from holmes.models import Worker
from tests.unit.base import ApiTestCase
from tests.fixtures import WorkerFactory


class TestWorkerStateHandler(ApiTestCase):

    @gen_test
    def test_worker_start_working(self):
        worker = WorkerFactory.create()
        self.db.flush()

        response = yield self.http_client.fetch(
            self.get_url('/worker/%s/start' % str(worker.uuid)),
            method='POST',
            body='http://www.globo.com/'
        )

        worker = Worker.by_uuid(worker.uuid, self.db)

        expect(worker).not_to_be_null()
        expect(response.code).to_equal(200)
        expect(response.body).to_be_like('OK')
        expect(str(worker.current_url)).to_equal('http://www.globo.com/')

    @gen_test
    def test_worker_start_working_invalid_worker(self):
        try:
            yield self.http_client.fetch(
                self.get_url('/worker/%s/start/' % self.ZERO_UUID),
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
                self.get_url('/worker/%s/start' % str(worker.uuid)),
                method='POST',
                body=''
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(400)
            expect(err.response.reason).to_be_like('Invalid URL')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_worker_complete_work(self):
        worker = WorkerFactory.create(current_url="http://www.globo.com/")
        self.db.flush()

        response = yield self.http_client.fetch(
            self.get_url('/worker/%s/complete' % str(worker.uuid)),
            method='POST',
            body=''
        )

        worker = Worker.by_uuid(worker.uuid, self.db)

        expect(worker).not_to_be_null()
        expect(response.code).to_equal(200)
        expect(response.body).to_be_like('OK')
        expect(worker.current_url).to_be_null()

    @gen_test
    def test_worker_complete_work_invalid_worker(self):
        try:
            yield self.http_client.fetch(
                self.get_url('/worker/%s/complete' % self.ZERO_UUID),
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
