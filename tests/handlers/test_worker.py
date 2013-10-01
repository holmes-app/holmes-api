#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from uuid import uuid4
from datetime import datetime
from ujson import loads

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError

from holmes.models import Worker, Page
from tests.base import ApiTestCase
from tests.fixtures import WorkerFactory, DomainFactory, PageFactory


class TestWorkerHandler(ApiTestCase):

    @gen_test
    def test_worker_ping_can_ping_new_worker(self):
        worker_uuid = uuid4()

        response = yield self.http_client.fetch(
            self.get_url('/worker/%s/ping' % str(worker_uuid)),
            method='POST',
            body=''
        )

        workers = yield Worker.objects.filter(uuid=worker_uuid).find_all()

        expect(workers).to_length(1)

        worker = workers[0]
        expect(response.code).to_equal(200)
        expect(response.body).to_be_like(str(worker.uuid))

    @gen_test
    def test_worker_ping_can_ping_existing_worker(self):
        date = datetime(2013, 9, 26, 17, 45, 0)

        worker = yield WorkerFactory.create(last_ping=date)

        response = yield self.http_client.fetch(
            self.get_url('/worker/%s/ping' % str(worker.uuid)),
            method='POST',
            body='current_page=%s' % str(worker.current_page)
        )

        workers = yield Worker.objects.filter(uuid=worker.uuid).find_all()
        
        expect(workers).to_length(1)

        worker = workers[0]
        expect(response.code).to_equal(200)
        expect(response.body).to_be_like(str(worker.uuid))
        expect(worker.last_ping).to_be_greater_than(date)

    @gen_test
    def test_worker_next_invalid_worker(self):
        try:
            yield self.http_client.fetch(
                self.get_url('/worker/%s/next' % "00000000-0000-0000-0000-000000000000")
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like("Worker not found")
        else:
            assert False, "Should not have got this far"

    @gen_test
    def test_worker_next_page_without_page(self):
        pages = yield Page.objects.find_all()
        for page in pages:
            page.delete()

        worker = yield WorkerFactory.create()

        try:
            yield self.http_client.fetch(
                self.get_url('/worker/%s/next' % str(worker.uuid))
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like("None available")
        else:
            assert False, "Should not have got this far"

    @gen_test
    def test_worker_get_next(self):
        pages = yield Page.objects.find_all()
        for page in pages:
            page.delete()

        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        worker = yield WorkerFactory.create(current_page=page)

        response = yield self.http_client.fetch(
            self.get_url('/worker/%s/next' % str(worker.uuid))
        )

        returned_json = loads(response.body)
        expect(returned_json).not_to_be_null()
        expect(returned_json['uuid']).to_equal(str(page.uuid))
        expect(page.added_date).not_to_equal(page.updated_date)
        expect(worker.current_page).to_equal(page)

    @gen_test
    def test_workers_list(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        worker = yield WorkerFactory.create(current_page=page)

        response = yield self.http_client.fetch(
            self.get_url('/workers/'),
        )

        expect(response.code).to_equal(200)

        workers = yield Worker.objects.filter().find_all()

        returned_json = loads(response.body)
        expect(returned_json).to_length(len(workers))

        #expect(returned_json[0]['uuid']).to_equal(str(worker.uuid))
        #expect(returned_json[0]['current_page']).to_equal(page.url)

